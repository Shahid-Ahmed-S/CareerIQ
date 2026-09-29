from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.services import JobService, AuthService, ProfileService
from app.models.models import Job, Application, User
from app.extensions import db

recruiter_bp = Blueprint("recruiter", __name__)

def require_recruiter():
    uid  = int(get_jwt_identity())
    user = AuthService.get_by_id(uid)
    if not user or user.role not in ("recruiter","admin"):
        return None, ({"error":"Recruiter access required."}, 403)
    return user, None

@recruiter_bp.get("/dashboard")
@jwt_required()
def dashboard():
    user, err = require_recruiter()
    if err: return jsonify(err[0]), err[1]
    jobs   = Job.query.filter_by(posted_by=user.id, is_active=True).all()
    total_apps = sum(len(j.applications) for j in jobs)
    return jsonify({"jobs_posted": len(jobs), "total_applications": total_apps,
                    "jobs": [j.to_dict() for j in jobs[:5]]})

@recruiter_bp.post("/jobs")
@jwt_required()
def post_job():
    user, err = require_recruiter()
    if err: return jsonify(err[0]), err[1]
    d = request.get_json() or {}
    if not d.get("title"): return jsonify({"error":"title required."}), 400
    res = JobService.create(d, posted_by=user.id)
    return jsonify({"message":"Job posted.","job":res["job"].to_dict()}), 201

@recruiter_bp.get("/jobs")
@jwt_required()
def my_jobs():
    user, err = require_recruiter()
    if err: return jsonify(err[0]), err[1]
    jobs = Job.query.filter_by(posted_by=user.id).order_by(Job.posted_at.desc()).all()
    return jsonify({"jobs":[j.to_dict() for j in jobs]})

@recruiter_bp.get("/jobs/<int:jid>/applicants")
@jwt_required()
def applicants(jid):
    user, err = require_recruiter()
    if err: return jsonify(err[0]), err[1]
    job = Job.query.filter_by(id=jid, posted_by=user.id).first()
    if not job: return jsonify({"error":"Not found."}), 404
    apps = Application.query.filter_by(job_id=jid).all()
    result = []
    for a in apps:
        u  = a.user
        sk = ProfileService.get_skills(u.id)
        result.append({"application_id":a.id,"status":a.status,
                        "applied_at":a.applied_at.isoformat(),
                        "user":{"id":u.id,"full_name":u.full_name,
                                "headline":u.profile.headline if u.profile else ""},
                        "skills":[s.to_dict() for s in sk]})
    return jsonify({"applicants":result})

@recruiter_bp.patch("/applicants/<int:aid>")
@jwt_required()
def update_applicant(aid):
    user, err = require_recruiter()
    if err: return jsonify(err[0]), err[1]
    a = Application.query.get(aid)
    if not a: return jsonify({"error":"Not found."}), 404
    d = request.get_json() or {}
    if "status" in d and d["status"] in Application.STAGES:
        a.status = d["status"]
    if "notes" in d: a.notes = d["notes"]
    db.session.commit()
    return jsonify({"message":"Updated.","application":a.to_dict()})

@recruiter_bp.get("/candidates")
@jwt_required()
def search_candidates():
    user, err = require_recruiter()
    if err: return jsonify(err[0]), err[1]
    skill_q = request.args.get("skill","").strip()
    loc_q   = request.args.get("location","").strip()
    q = User.query.filter_by(role="user", is_active=True)
    if loc_q:
        from app.models.models import Profile
        q = q.join(Profile).filter(Profile.location.ilike(f"%{loc_q}%"))
    users = q.limit(30).all()
    result = []
    for u in users:
        sk = [s.to_dict() for s in ProfileService.get_skills(u.id)]
        if skill_q and not any(skill_q.lower() in s["skill_name"].lower() for s in sk):
            continue
        result.append({"id":u.id,"full_name":u.full_name,
                        "avatar":u.full_name[0].upper(),
                        "headline":u.profile.headline if u.profile else "",
                        "location":u.profile.location if u.profile else "",
                        "skills":sk[:6]})
    return jsonify({"candidates":result})
