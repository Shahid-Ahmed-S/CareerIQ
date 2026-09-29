from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models.models import SavedJob, Job

saved_jobs_bp = Blueprint("saved_jobs", __name__)

@saved_jobs_bp.post("/")
@jwt_required()
def save():
    uid = int(get_jwt_identity())
    d   = request.get_json() or {}
    if not d.get("job_id"): return jsonify({"error": "job_id required."}), 400
    if not Job.query.get(d["job_id"]): return jsonify({"error": "Job not found."}), 404
    if SavedJob.query.filter_by(user_id=uid, job_id=d["job_id"]).first():
        return jsonify({"error": "Already saved."}), 409
    s = SavedJob(user_id=uid, job_id=d["job_id"])
    db.session.add(s); db.session.commit()
    return jsonify({"message": "Saved.", "saved_job": s.to_dict()}), 201

@saved_jobs_bp.get("/")
@jwt_required()
def list_saved():
    uid  = int(get_jwt_identity())
    jobs = SavedJob.query.filter_by(user_id=uid).order_by(SavedJob.saved_at.desc()).all()
    return jsonify({"saved_jobs": [j.to_dict() for j in jobs]})

@saved_jobs_bp.get("/ids")
@jwt_required()
def saved_ids():
    uid = int(get_jwt_identity())
    return jsonify({"saved_job_ids": [s.job_id for s in SavedJob.query.filter_by(user_id=uid).all()]})

@saved_jobs_bp.delete("/<int:jid>")
@jwt_required()
def unsave(jid):
    uid = int(get_jwt_identity())
    s   = SavedJob.query.filter_by(user_id=uid, job_id=jid).first()
    if not s: return jsonify({"error": "Not found."}), 404
    db.session.delete(s); db.session.commit()
    return jsonify({"message": "Removed."})
