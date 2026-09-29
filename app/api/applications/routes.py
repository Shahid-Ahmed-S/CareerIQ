from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models.models import Application, Job

applications_bp = Blueprint("applications", __name__)

@applications_bp.post("/")
@jwt_required()
def apply():
    uid = int(get_jwt_identity())
    d   = request.get_json() or {}
    if not d.get("job_id"): return jsonify({"error": "job_id required."}), 400
    if not Job.query.get(d["job_id"]): return jsonify({"error": "Job not found."}), 404
    if Application.query.filter_by(user_id=uid, job_id=d["job_id"]).first():
        return jsonify({"error": "Already applied to this job."}), 409
    a = Application(user_id=uid, job_id=d["job_id"], notes=d.get("notes",""))
    db.session.add(a); db.session.commit()
    return jsonify({"message": "Tracked.", "application": a.to_dict()}), 201

@applications_bp.get("/")
@jwt_required()
def list_apps():
    uid = int(get_jwt_identity())
    status = request.args.get("status")
    q = Application.query.filter_by(user_id=uid)
    if status: q = q.filter_by(status=status)
    apps = q.order_by(Application.applied_at.desc()).all()
    return jsonify({"applications": [a.to_dict() for a in apps],
                    "counts": {s: Application.query.filter_by(user_id=uid,status=s).count()
                               for s in Application.STAGES}})

@applications_bp.patch("/<int:aid>")
@jwt_required()
def update_app(aid):
    uid = int(get_jwt_identity())
    a   = Application.query.filter_by(id=aid, user_id=uid).first()
    if not a: return jsonify({"error": "Not found."}), 404
    d = request.get_json() or {}
    if "status" in d:
        if d["status"] not in Application.STAGES:
            return jsonify({"error": f"Invalid status."}), 400
        a.status = d["status"]
    if "notes" in d: a.notes = d["notes"]
    db.session.commit()
    return jsonify({"message": "Updated.", "application": a.to_dict()})

@applications_bp.delete("/<int:aid>")
@jwt_required()
def delete_app(aid):
    uid = int(get_jwt_identity())
    a   = Application.query.filter_by(id=aid, user_id=uid).first()
    if not a: return jsonify({"error": "Not found."}), 404
    db.session.delete(a); db.session.commit()
    return jsonify({"message": "Removed."})
