import os
import random
import logging
from datetime import datetime, timedelta
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from app.extensions import db, bcrypt
from app.models.models import User, Profile, Skill, UserSkill, Job, JobSkill

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
#  Auth Service
# ─────────────────────────────────────────────
class AuthService:

    @staticmethod
    def register(email, password, full_name):
        if User.query.filter_by(email=email.lower()).first():
            return {"success": False, "error": "Email already registered."}
        hashed = bcrypt.generate_password_hash(password).decode("utf-8")
        user = User(email=email.lower().strip(), password_hash=hashed, full_name=full_name.strip())
        db.session.add(user)
        db.session.flush()
        db.session.add(Profile(user_id=user.id))
        db.session.commit()
        return {"success": True, "user": user}

    @staticmethod
    def login(email, password):
        user = User.query.filter_by(email=email.lower()).first()
        if not user or not user.is_active:
            return {"success": False, "error": "Invalid email or password."}
        if not bcrypt.check_password_hash(user.password_hash, password):
            return {"success": False, "error": "Invalid email or password."}
        return {"success": True, "user": user}

    @staticmethod
    def get_by_id(uid):   return User.query.get(uid)
    @staticmethod
    def get_by_email(em): return User.query.filter_by(email=em.lower()).first()

    @staticmethod
    def change_password(uid, old_pw, new_pw):
        user = User.query.get(uid)
        if not user: return {"success": False, "error": "User not found."}
        if not bcrypt.check_password_hash(user.password_hash, old_pw):
            return {"success": False, "error": "Current password is incorrect."}
        user.password_hash = bcrypt.generate_password_hash(new_pw).decode("utf-8")
        db.session.commit()
        return {"success": True}


# ─────────────────────────────────────────────
#  Email Service
# ─────────────────────────────────────────────
class EmailService:

    def _serializer(self):
        return URLSafeTimedSerializer(os.getenv("SECRET_KEY", "careeriq-secret-dev-2024"))

    def make_token(self, email):
        return self._serializer().dumps(email, salt="email-verify")

    def verify_token(self, token, max_age=3600):
        try:
            email = self._serializer().loads(token, salt="email-verify", max_age=max_age)
            return {"success": True, "email": email}
        except SignatureExpired:
            return {"success": False, "error": "Link expired."}
        except BadSignature:
            return {"success": False, "error": "Invalid link."}

    def send_verification(self, to_email, full_name, token):
        base  = os.getenv("APP_BASE_URL", "http://localhost:5001")
        link  = f"{base}/api/auth/verify-email/{token}"
        api_key = os.getenv("SENDGRID_API_KEY", "")

        if api_key:
            try:
                import sendgrid
                from sendgrid.helpers.mail import Mail, Email, To
                sg = sendgrid.SendGridAPIClient(api_key=api_key)
                html = f"""<div style="font-family:sans-serif;max-width:520px;margin:0 auto;padding:32px;background:#0f1117;color:#e8ecf4;border-radius:12px">
                  <h2>Hi {full_name.split()[0]}, verify your email 👋</h2>
                  <p style="color:#9ba3be">Click below to activate your CareerIQ account.</p>
                  <a href="{link}" style="display:inline-block;background:#6c8aff;color:#fff;padding:12px 28px;border-radius:8px;font-weight:600;text-decoration:none;margin:16px 0">Verify Email</a>
                  <p style="color:#5c6480;font-size:12px">Link expires in 1 hour. If you didn't sign up, ignore this.</p>
                </div>"""
                sg.send(Mail(from_email=Email("noreply@careeriq.com","CareerIQ"),
                             to_emails=To(to_email),
                             subject="Verify your CareerIQ email",
                             html_content=html))
                return {"success": True}
            except Exception as e:
                logger.error(f"SendGrid error: {e}")

        # Dev fallback
        print(f"\n📧 [DEV] Verify email for {to_email}:\n   {link}\n")
        return {"success": True, "dev_mode": True, "verify_url": link}


email_service = EmailService()


# ─────────────────────────────────────────────
#  OTP Service
# ─────────────────────────────────────────────
class OTPService:

    def send_otp(self, user, phone):
        otp    = str(random.randint(100000, 999999))
        expiry = datetime.utcnow() + timedelta(minutes=10)
        user.phone_number    = phone
        user.phone_otp       = otp
        user.phone_otp_expiry= expiry
        db.session.commit()
        print(f"\n📱 [DEV] OTP for {phone}: {otp}  (valid 10 min)\n")
        return {"success": True, "dev_mode": True, "otp": otp}

    def verify_otp(self, user, otp):
        if not user.phone_otp:
            return {"success": False, "error": "No OTP requested."}
        if datetime.utcnow() > user.phone_otp_expiry:
            return {"success": False, "error": "OTP expired."}
        if user.phone_otp != otp.strip():
            return {"success": False, "error": "Incorrect OTP."}
        user.phone_verified    = True
        user.phone_otp         = None
        user.phone_otp_expiry  = None
        db.session.commit()
        return {"success": True}


otp_service = OTPService()


# ─────────────────────────────────────────────
#  Profile Service
# ─────────────────────────────────────────────
class ProfileService:

    @staticmethod
    def get(uid): return Profile.query.filter_by(user_id=uid).first()

    @staticmethod
    def update(uid, data):
        p = Profile.query.filter_by(user_id=uid).first()
        if not p: return {"success": False, "error": "Profile not found."}
        for f in ["headline","bio","location","years_experience","current_role",
                  "desired_role","linkedin_url","github_url","resume_url"]:
            if f in data: setattr(p, f, data[f])
        db.session.commit()
        return {"success": True, "profile": p}

    @staticmethod
    def get_skills(uid):
        return UserSkill.query.filter_by(user_id=uid).join(Skill).all()

    @staticmethod
    def add_skill(uid, name, proficiency=1, years=0.0):
        norm  = name.strip().lower()
        skill = Skill.query.filter_by(normalized_name=norm).first()
        if not skill:
            skill = Skill(name=name.strip(), normalized_name=norm)
            db.session.add(skill)
            db.session.flush()
        if UserSkill.query.filter_by(user_id=uid, skill_id=skill.id).first():
            return {"success": False, "error": "Skill already added."}
        us = UserSkill(user_id=uid, skill_id=skill.id,
                       proficiency_level=max(1,min(4,proficiency)),
                       years_used=max(0.0,years))
        db.session.add(us)
        db.session.commit()
        return {"success": True, "user_skill": us}

    @staticmethod
    def remove_skill(uid, skill_id):
        us = UserSkill.query.filter_by(user_id=uid, skill_id=skill_id).first()
        if not us: return {"success": False, "error": "Skill not found."}
        db.session.delete(us)
        db.session.commit()
        return {"success": True}

    @staticmethod
    def update_skill(uid, skill_id, proficiency=None, years=None):
        us = UserSkill.query.filter_by(user_id=uid, skill_id=skill_id).first()
        if not us: return {"success": False, "error": "Skill not found."}
        if proficiency is not None: us.proficiency_level = max(1,min(4,proficiency))
        if years is not None:       us.years_used        = max(0.0,years)
        db.session.commit()
        return {"success": True, "user_skill": us}


# ─────────────────────────────────────────────
#  Job Service
# ─────────────────────────────────────────────
class JobService:

    @staticmethod
    def list_jobs(filters=None, page=1, per_page=12):
        q = Job.query.filter_by(is_active=True)
        if filters:
            if filters.get("title"):            q = q.filter(Job.title.ilike(f"%{filters['title']}%"))
            if filters.get("location"):         q = q.filter(Job.location.ilike(f"%{filters['location']}%"))
            if filters.get("job_type"):         q = q.filter_by(job_type=filters["job_type"])
            if filters.get("experience_level"): q = q.filter_by(experience_level=filters["experience_level"])
        return q.order_by(Job.posted_at.desc()).paginate(page=page, per_page=per_page, error_out=False)

    @staticmethod
    def get(jid): return Job.query.get(jid)

    @staticmethod
    def create(data, posted_by=None):
        job = Job(
            title=data["title"], company=data.get("company"),
            location=data.get("location"), job_type=data.get("job_type","full-time"),
            experience_level=data.get("experience_level","mid"),
            description=data.get("description"),
            salary_min=data.get("salary_min"), salary_max=data.get("salary_max"),
            source=data.get("source","manual"), source_url=data.get("source_url"),
            posted_by=posted_by,
        )
        db.session.add(job)
        db.session.flush()
        for sd in data.get("skills", []):
            norm  = sd["name"].strip().lower()
            skill = Skill.query.filter_by(normalized_name=norm).first()
            if not skill:
                skill = Skill(name=sd["name"].strip(), normalized_name=norm)
                db.session.add(skill)
                db.session.flush()
            db.session.add(JobSkill(job_id=job.id, skill_id=skill.id,
                                    required_level=sd.get("required_level",1),
                                    is_required=sd.get("is_required",True)))
        db.session.commit()
        return {"success": True, "job": job}


class AuthServiceV2(AuthService):
    @staticmethod
    def register(email, password, full_name, role="user"):
        from app.extensions import db, bcrypt
        from app.models.models import User, Profile
        if User.query.filter_by(email=email.lower()).first():
            return {"success": False, "error": "Email already registered."}
        hashed = bcrypt.generate_password_hash(password).decode("utf-8")
        user = User(email=email.lower().strip(), password_hash=hashed,
                    full_name=full_name.strip(),
                    role=role if role in ("user","recruiter") else "user")
        db.session.add(user)
        db.session.flush()
        db.session.add(Profile(user_id=user.id))
        db.session.commit()
        return {"success": True, "user": user}
