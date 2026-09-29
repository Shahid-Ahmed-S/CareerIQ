import os
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.services import ProfileService, AuthService
from app.engines.engines import resume_parser

profile_bp = Blueprint("profile", __name__)
# UPLOAD_DIR resolved at request time using current_app.static_folder
UPLOAD_DIR = None  # set per-request below

@profile_bp.get("/")
@jwt_required()
def get_profile():
    p = ProfileService.get(int(get_jwt_identity()))
    if not p: return jsonify({"error": "Not found."}), 404
    return jsonify({"profile": p.to_dict()})

@profile_bp.put("/")
@jwt_required()
def update_profile():
    res = ProfileService.update(int(get_jwt_identity()), request.get_json() or {})
    if not res["success"]: return jsonify({"error": res["error"]}), 400
    return jsonify({"message": "Profile updated.", "profile": res["profile"].to_dict()})

@profile_bp.get("/completeness")
@jwt_required()
def completeness():
    user = AuthService.get_by_id(int(get_jwt_identity()))
    return jsonify({"score": user.completeness_score(), "tips": user.completeness_tips()})

@profile_bp.get("/skills")
@jwt_required()
def get_skills():
    skills = ProfileService.get_skills(int(get_jwt_identity()))
    return jsonify({"skills": [s.to_dict() for s in skills]})

@profile_bp.post("/skills")
@jwt_required()
def add_skill():
    d = request.get_json() or {}
    if not d.get("skill_name"): return jsonify({"error": "skill_name required."}), 400
    res = ProfileService.add_skill(int(get_jwt_identity()), d["skill_name"],
                                    proficiency=d.get("proficiency_level",1),
                                    years=d.get("years_used",0.0))
    if not res["success"]: return jsonify({"error": res["error"]}), 409
    return jsonify({"message": "Skill added.", "skill": res["user_skill"].to_dict()}), 201

@profile_bp.delete("/skills/<int:skill_id>")
@jwt_required()
def remove_skill(skill_id):
    res = ProfileService.remove_skill(int(get_jwt_identity()), skill_id)
    if not res["success"]: return jsonify({"error": res["error"]}), 404
    return jsonify({"message": "Skill removed."})

@profile_bp.patch("/skills/<int:skill_id>")
@jwt_required()
def update_skill(skill_id):
    d   = request.get_json() or {}
    res = ProfileService.update_skill(int(get_jwt_identity()), skill_id,
                                       proficiency=d.get("proficiency_level"),
                                       years=d.get("years_used"))
    if not res["success"]: return jsonify({"error": res["error"]}), 404
    return jsonify({"message": "Skill updated.", "skill": res["user_skill"].to_dict()})

@profile_bp.post("/upload-resume")
@jwt_required()
def upload_resume():
    uid = int(get_jwt_identity())
    if "resume" not in request.files:
        return jsonify({"error": "No file. Use field name 'resume'."}), 400
    file = request.files["resume"]
    if not file.filename: return jsonify({"error": "No file selected."}), 400
    ext = file.filename.rsplit(".",1)[-1].lower()
    if ext not in ("pdf","docx"): return jsonify({"error": "Upload PDF or DOCX."}), 400
    from flask import current_app
    upload_dir = os.path.join(current_app.static_folder, "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    fname = f"resume_{uid}.{ext}"
    path  = os.path.join(upload_dir, fname)
    file.save(path)
    parsed = resume_parser.parse(path)
    if not parsed["success"]: return jsonify({"error": parsed["error"]}), 422
    ProfileService.update(uid, {"resume_url": f"/static/uploads/{fname}"})
    added = []
    for s in parsed["skills"]:
        r = ProfileService.add_skill(uid, s["name"], proficiency=s["proficiency_level"])
        if r["success"]: added.append(s["name"])
    return jsonify({"message": "Resume parsed.", "skills_added": added,
                    "experience": parsed["experience"],
                    "resume_url": f"/static/uploads/{fname}"})

@profile_bp.get("/public/<int:user_id>")
@jwt_required()
def public_profile(user_id):
    user = AuthService.get_by_id(user_id)
    if not user: return jsonify({"error": "User not found."}), 404
    skills = ProfileService.get_skills(user_id)
    return jsonify({
        "user": {"id": user.id, "full_name": user.full_name,
                 "avatar": user.full_name[0].upper()},
        "profile": user.profile.to_dict() if user.profile else {},
        "skills": [s.to_dict() for s in skills],
    })


@profile_bp.post("/upload-avatar")
@jwt_required()
def upload_avatar():
    import os, uuid
    from flask import current_app
    from app.extensions import db
    from app.models.models import User
    uid = int(get_jwt_identity())

    if "avatar" not in request.files:
        return jsonify({"error": "No file. Use field name 'avatar'."}), 400
    file = request.files["avatar"]
    ext  = (file.filename or "").rsplit(".", 1)[-1].lower()
    if ext not in ("jpg", "jpeg", "png", "gif", "webp"):
        return jsonify({"error": "Use JPG, PNG, GIF or WEBP."}), 400

    upload_dir = os.path.join(current_app.static_folder, "uploads", "avatars")
    os.makedirs(upload_dir, exist_ok=True)
    fname = f"avatar_{uid}_{uuid.uuid4().hex[:6]}.{ext}"
    file.save(os.path.join(upload_dir, fname))

    user = User.query.get(uid)
    user.avatar_url = f"/static/uploads/avatars/{fname}"
    db.session.commit()

    # Update session cache
    return jsonify({"message": "Avatar updated.", "avatar_url": user.avatar_url})
