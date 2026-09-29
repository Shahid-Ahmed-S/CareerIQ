from app.extensions import db
from datetime import datetime


# ─────────────────────────────────────────────
#  User
# ─────────────────────────────────────────────
class User(db.Model):
    __tablename__ = "users"
    id                = db.Column(db.Integer, primary_key=True)
    email             = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash     = db.Column(db.String(255), nullable=False)
    full_name         = db.Column(db.String(100), nullable=False)
    role              = db.Column(db.String(20), default="user")  # user | recruiter | admin
    avatar_url        = db.Column(db.String(300))
    email_verified    = db.Column(db.Boolean, default=False)
    phone_number      = db.Column(db.String(20))
    phone_verified    = db.Column(db.Boolean, default=False)
    phone_otp         = db.Column(db.String(6))
    phone_otp_expiry  = db.Column(db.DateTime)
    is_active         = db.Column(db.Boolean, default=True)
    created_at        = db.Column(db.DateTime, default=datetime.utcnow)

    profile        = db.relationship("Profile",       backref="user", uselist=False, cascade="all, delete-orphan")
    user_skills    = db.relationship("UserSkill",     backref="user", cascade="all, delete-orphan")
    posts          = db.relationship("Post",          backref="author", foreign_keys="Post.user_id", cascade="all, delete-orphan")
    applications   = db.relationship("Application",  backref="user", cascade="all, delete-orphan")
    saved_jobs     = db.relationship("SavedJob",     backref="user", cascade="all, delete-orphan")
    sent_requests  = db.relationship("Connection",   foreign_keys="Connection.sender_id",   backref="sender",   cascade="all, delete-orphan")
    recv_requests  = db.relationship("Connection",   foreign_keys="Connection.receiver_id", backref="receiver", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id, "email": self.email, "full_name": self.full_name,
            "role": self.role, "email_verified": self.email_verified,
            "phone_number": self.phone_number, "phone_verified": self.phone_verified,
            "avatar_url": self.avatar_url, "is_active": self.is_active, "created_at": self.created_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }

    def completeness_score(self):
        score = 0
        checks = [
            (bool(self.full_name), 10),
            (bool(self.email_verified), 10),
            (bool(self.phone_verified), 5),
            (bool(self.profile and self.profile.headline), 10),
            (bool(self.profile and self.profile.bio), 10),
            (bool(self.profile and self.profile.location), 5),
            (bool(self.profile and self.profile.current_role), 10),
            (bool(self.profile and self.profile.desired_role), 10),
            (bool(self.profile and self.profile.linkedin_url), 5),
            (bool(self.profile and self.profile.resume_url), 10),
            (len(self.user_skills) >= 3, 15),
        ]
        for cond, pts in checks:
            if cond:
                score += pts
        return min(score, 100)

    def completeness_tips(self):
        tips = []
        if not self.email_verified:           tips.append("Verify your email address")
        if not self.phone_verified:           tips.append("Verify your phone number")
        if self.profile:
            if not self.profile.headline:     tips.append("Add a professional headline")
            if not self.profile.bio:          tips.append("Write a short bio")
            if not self.profile.location:     tips.append("Add your location")
            if not self.profile.current_role: tips.append("Add your current role")
            if not self.profile.desired_role: tips.append("Set your desired role")
            if not self.profile.resume_url:   tips.append("Upload your resume")
        if len(self.user_skills) < 3:         tips.append("Add at least 3 skills")
        return tips[:3]


# ─────────────────────────────────────────────
#  Profile
# ─────────────────────────────────────────────
class Profile(db.Model):
    __tablename__ = "profiles"
    id               = db.Column(db.Integer, primary_key=True)
    user_id          = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    headline         = db.Column(db.String(200))
    bio              = db.Column(db.Text)
    location         = db.Column(db.String(100))
    years_experience = db.Column(db.Float, default=0.0)
    current_role     = db.Column(db.String(100))
    desired_role     = db.Column(db.String(100))
    resume_url       = db.Column(db.String(300))
    linkedin_url     = db.Column(db.String(300))
    github_url       = db.Column(db.String(300))
    updated_at       = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id, "user_id": self.user_id,
            "headline": self.headline, "bio": self.bio,
            "location": self.location, "years_experience": self.years_experience,
            "current_role": self.current_role, "desired_role": self.desired_role,
            "resume_url": self.resume_url,
            "linkedin_url": self.linkedin_url, "github_url": self.github_url,
        }


# ─────────────────────────────────────────────
#  Skills
# ─────────────────────────────────────────────
class Skill(db.Model):
    __tablename__ = "skills"
    id              = db.Column(db.Integer, primary_key=True)
    name            = db.Column(db.String(100), unique=True, nullable=False)
    normalized_name = db.Column(db.String(100), unique=True, nullable=False)
    category        = db.Column(db.String(50), default="General")
    user_skills     = db.relationship("UserSkill", backref="skill", cascade="all, delete-orphan")
    job_skills      = db.relationship("JobSkill",  backref="skill", cascade="all, delete-orphan")

    def to_dict(self):
        return {"id": self.id, "name": self.name, "category": self.category}


class UserSkill(db.Model):
    __tablename__ = "user_skills"
    id               = db.Column(db.Integer, primary_key=True)
    user_id          = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    skill_id         = db.Column(db.Integer, db.ForeignKey("skills.id"), nullable=False)
    proficiency_level= db.Column(db.Integer, default=1)
    years_used       = db.Column(db.Float,   default=0.0)
    added_at         = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint("user_id", "skill_id", name="uq_user_skill"),)

    def to_dict(self):
        return {
            "skill_id": self.skill_id,
            "skill_name": self.skill.name if self.skill else None,
            "category": self.skill.category if self.skill else None,
            "proficiency_level": self.proficiency_level,
            "years_used": self.years_used,
        }


# ─────────────────────────────────────────────
#  Jobs
# ─────────────────────────────────────────────
class Job(db.Model):
    __tablename__ = "jobs"
    id               = db.Column(db.Integer, primary_key=True)
    title            = db.Column(db.String(200), nullable=False)
    company          = db.Column(db.String(150))
    location         = db.Column(db.String(100))
    job_type         = db.Column(db.String(30), default="full-time")
    experience_level = db.Column(db.String(30), default="mid")
    description      = db.Column(db.Text)
    salary_min       = db.Column(db.Integer)
    salary_max       = db.Column(db.Integer)
    source           = db.Column(db.String(50), default="manual")
    source_url       = db.Column(db.String(500))
    posted_by        = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    is_active        = db.Column(db.Boolean, default=True)
    posted_at        = db.Column(db.DateTime, default=datetime.utcnow)
    job_skills       = db.relationship("JobSkill", backref="job", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id, "title": self.title, "company": self.company,
            "location": self.location, "job_type": self.job_type,
            "experience_level": self.experience_level,
            "description": self.description,
            "salary_min": self.salary_min, "salary_max": self.salary_max,
            "source_url": self.source_url,
            "posted_at": self.posted_at.strftime("%Y-%m-%dT%H:%M:%SZ") if self.posted_at else None,
            "skills": [js.to_dict() for js in self.job_skills],
        }


class JobSkill(db.Model):
    __tablename__ = "job_skills"
    id             = db.Column(db.Integer, primary_key=True)
    job_id         = db.Column(db.Integer, db.ForeignKey("jobs.id"), nullable=False)
    skill_id       = db.Column(db.Integer, db.ForeignKey("skills.id"), nullable=False)
    required_level = db.Column(db.Integer, default=1)
    is_required    = db.Column(db.Boolean, default=True)
    __table_args__ = (db.UniqueConstraint("job_id", "skill_id", name="uq_job_skill"),)

    def to_dict(self):
        return {
            "skill_id": self.skill_id,
            "skill_name": self.skill.name if self.skill else None,
            "required_level": self.required_level,
            "is_required": self.is_required,
        }


# ─────────────────────────────────────────────
#  Recommendations & Skill Gap
# ─────────────────────────────────────────────
class Recommendation(db.Model):
    __tablename__ = "recommendations"
    id           = db.Column(db.Integer, primary_key=True)
    user_id      = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    job_id       = db.Column(db.Integer, db.ForeignKey("jobs.id"), nullable=True)
    rec_type     = db.Column(db.String(20))
    title        = db.Column(db.String(200))
    description  = db.Column(db.Text)
    url          = db.Column(db.String(500))
    score        = db.Column(db.Float, default=0.0)
    reason       = db.Column(db.Text)
    is_dismissed = db.Column(db.Boolean, default=False)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)
    user         = db.relationship("User", backref="recommendations")
    job          = db.relationship("Job",  backref="recommendations")

    def to_dict(self):
        return {
            "id": self.id, "rec_type": self.rec_type, "title": self.title,
            "description": self.description, "url": self.url,
            "score": round(self.score, 2), "reason": self.reason,
            "is_dismissed": self.is_dismissed,
            "created_at": self.created_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }


class SkillGapReport(db.Model):
    __tablename__ = "skill_gap_reports"
    id                = db.Column(db.Integer, primary_key=True)
    user_id           = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    target_role       = db.Column(db.String(150), nullable=False)
    overall_gap_score = db.Column(db.Float, default=0.0)
    gap_details       = db.Column(db.JSON, default=list)
    learning_path     = db.Column(db.JSON, default=list)
    created_at        = db.Column(db.DateTime, default=datetime.utcnow)
    user              = db.relationship("User", backref="skill_gap_reports")

    def to_dict(self):
        return {
            "id": self.id, "target_role": self.target_role,
            "overall_gap_score": round(self.overall_gap_score, 2),
            "gap_details": self.gap_details,
            "learning_path": self.learning_path,
            "created_at": self.created_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }


# ─────────────────────────────────────────────
#  Applications & Saved Jobs
# ─────────────────────────────────────────────
class Application(db.Model):
    __tablename__ = "applications"
    STAGES = ["applied","screening","interview","offer","rejected","withdrawn"]
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    job_id     = db.Column(db.Integer, db.ForeignKey("jobs.id"),  nullable=False)
    status     = db.Column(db.String(30), default="applied")
    notes      = db.Column(db.Text)
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    job        = db.relationship("Job", backref="applications")
    __table_args__ = (db.UniqueConstraint("user_id","job_id",name="uq_user_job_app"),)

    def to_dict(self):
        return {
            "id": self.id, "job_id": self.job_id,
            "job": self.job.to_dict() if self.job else None,
            "status": self.status, "notes": self.notes,
            "applied_at": self.applied_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "updated_at": self.updated_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }


class SavedJob(db.Model):
    __tablename__ = "saved_jobs"
    id       = db.Column(db.Integer, primary_key=True)
    user_id  = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    job_id   = db.Column(db.Integer, db.ForeignKey("jobs.id"),  nullable=False)
    saved_at = db.Column(db.DateTime, default=datetime.utcnow)
    job      = db.relationship("Job", backref="saved_by")
    __table_args__ = (db.UniqueConstraint("user_id","job_id",name="uq_saved_job"),)

    def to_dict(self):
        return {
            "id": self.id, "job_id": self.job_id,
            "job": self.job.to_dict() if self.job else None,
            "saved_at": self.saved_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }


# ─────────────────────────────────────────────
#  Posts / Feed
# ─────────────────────────────────────────────
class Post(db.Model):
    __tablename__ = "posts"
    id                = db.Column(db.Integer, primary_key=True)
    user_id           = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    content           = db.Column(db.Text, nullable=False)
    post_type         = db.Column(db.String(30), default="post")
    achievement_title = db.Column(db.String(200))
    achievement_icon  = db.Column(db.String(10), default="🏆")
    media_url         = db.Column(db.String(500))
    media_type        = db.Column(db.String(10))   # image | video
    is_deleted        = db.Column(db.Boolean, default=False)
    created_at        = db.Column(db.DateTime, default=datetime.utcnow)
    likes    = db.relationship("PostLike",    backref="post", cascade="all, delete-orphan")
    comments = db.relationship("PostComment", backref="post", cascade="all, delete-orphan",
                               order_by="PostComment.created_at")

    def like_count(self):    return len(self.likes)
    def comment_count(self): return len([c for c in self.comments if not c.is_deleted])
    def is_liked_by(self, uid): return any(l.user_id == uid for l in self.likes)

    def to_dict(self, current_user_id=None):
        a = self.author
        return {
            "id": self.id, "user_id": self.user_id,
            "author_name":       a.full_name if a else "Unknown",
            "author_avatar":     (a.full_name or "?")[0].upper() if a else "?",
            "author_avatar_url": a.avatar_url if a else None,
            "author_headline":   a.profile.headline if a and a.profile else "",
            "content": self.content, "post_type": self.post_type,
            "achievement_title": self.achievement_title,
            "achievement_icon":  self.achievement_icon,
            "media_url":   self.media_url,
            "media_type":  self.media_type,
            "like_count":    self.like_count(),
            "comment_count": self.comment_count(),
            "is_liked": self.is_liked_by(current_user_id) if current_user_id else False,
            "is_own":   self.user_id == current_user_id   if current_user_id else False,
            "created_at": self.created_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "comments": [c.to_dict() for c in self.comments if not c.is_deleted][:3],
        }


class PostLike(db.Model):
    __tablename__ = "post_likes"
    id         = db.Column(db.Integer, primary_key=True)
    post_id    = db.Column(db.Integer, db.ForeignKey("posts.id"), nullable=False)
    user_id    = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint("post_id","user_id",name="uq_post_like"),)


class PostComment(db.Model):
    __tablename__ = "post_comments"
    id         = db.Column(db.Integer, primary_key=True)
    post_id    = db.Column(db.Integer, db.ForeignKey("posts.id"), nullable=False)
    user_id    = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    content    = db.Column(db.Text, nullable=False)
    is_deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    author     = db.relationship("User", foreign_keys=[user_id])

    def to_dict(self):
        return {
            "id": self.id, "post_id": self.post_id, "user_id": self.user_id,
            "author_name":   self.author.full_name if self.author else "Unknown",
            "author_avatar": (self.author.full_name or "?")[0].upper() if self.author else "?",
            "content": self.content, "created_at": self.created_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }


# ─────────────────────────────────────────────
#  Connections & Messages
# ─────────────────────────────────────────────
class Connection(db.Model):
    __tablename__ = "connections"
    id          = db.Column(db.Integer, primary_key=True)
    sender_id   = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    status      = db.Column(db.String(20), default="pending")  # pending|accepted|rejected
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at  = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint("sender_id","receiver_id",name="uq_connection"),)

    def to_dict(self, current_user_id=None):
        other_id   = self.receiver_id if self.sender_id == current_user_id else self.sender_id
        other_user = User.query.get(other_id)
        return {
            "id": self.id,
            "sender_id": self.sender_id, "receiver_id": self.receiver_id,
            "status": self.status,
            "other_user": {
                "id": other_user.id,
                "full_name": other_user.full_name,
                "avatar": other_user.full_name[0].upper() if other_user else "?",
                "headline": other_user.profile.headline if other_user and other_user.profile else "",
            } if other_user else None,
            "created_at": self.created_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }


class Message(db.Model):
    __tablename__ = "messages"
    id          = db.Column(db.Integer, primary_key=True)
    sender_id   = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    content     = db.Column(db.Text, nullable=False)
    is_read     = db.Column(db.Boolean, default=False)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    sender      = db.relationship("User", foreign_keys=[sender_id])
    receiver    = db.relationship("User", foreign_keys=[receiver_id])

    def to_dict(self, current_user_id=None):
        return {
            "id": self.id,
            "sender_id":   self.sender_id,
            "receiver_id": self.receiver_id,
            "sender_name": self.sender.full_name if self.sender else "Unknown",
            "content":     self.content,
            "is_read":     self.is_read,
            "is_mine":     self.sender_id == current_user_id,
            "created_at":  self.created_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }


# ─────────────────────────────────────────────
#  Notifications
# ─────────────────────────────────────────────
class Notification(db.Model):
    __tablename__ = "notifications"
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    actor_id   = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    notif_type = db.Column(db.String(30))
    # like | comment | connection_request | connection_accepted | message | post
    title      = db.Column(db.String(200))
    body       = db.Column(db.String(400))
    link       = db.Column(db.String(200))
    is_read    = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user       = db.relationship("User", foreign_keys=[user_id], backref="notifications")
    actor      = db.relationship("User", foreign_keys=[actor_id])

    def to_dict(self):
        return {
            "id":         self.id,
            "notif_type": self.notif_type,
            "title":      self.title,
            "body":       self.body,
            "link":       self.link,
            "is_read":    self.is_read,
            "actor_avatar": (self.actor.full_name or "?")[0].upper() if self.actor else "?",
            "created_at": self.created_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
