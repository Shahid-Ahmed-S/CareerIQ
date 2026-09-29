from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.engines.engines import skill_gap_analyzer
from app.models.models import SkillGapReport
from app.extensions import db

skill_gap_bp = Blueprint("skill_gap", __name__)

@skill_gap_bp.post("/analyze")
@jwt_required()
def analyze():
    uid  = int(get_jwt_identity())
    role = (request.get_json() or {}).get("target_role","").strip()
    if not role: return jsonify({"error": "target_role required."}), 400
    res  = skill_gap_analyzer.analyze(uid, role)
    if not res["success"]: return jsonify({"error": res["error"]}), 404
    r = SkillGapReport(user_id=uid, target_role=res["target_role"],
                       overall_gap_score=res["overall_gap_score"],
                       gap_details=res["gap_details"], learning_path=res["learning_path"])
    db.session.add(r); db.session.commit()
    return jsonify({**res, "report_id": r.id})

@skill_gap_bp.get("/reports")
@jwt_required()
def reports():
    uid = int(get_jwt_identity())
    rs  = SkillGapReport.query.filter_by(user_id=uid).order_by(SkillGapReport.created_at.desc()).limit(10).all()
    return jsonify({"reports": [r.to_dict() for r in rs]})

@skill_gap_bp.get("/reports/<int:rid>")
@jwt_required()
def get_report(rid):
    uid = int(get_jwt_identity())
    r   = SkillGapReport.query.filter_by(id=rid, user_id=uid).first()
    if not r: return jsonify({"error": "Not found."}), 404
    return jsonify({"report": r.to_dict()})
