from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.engines.engines import recommendation_engine
from app.models.models import Recommendation
from app.extensions import db

rec_bp = Blueprint("recommendations", __name__)

@rec_bp.get("/jobs")
@jwt_required()
def recommend_jobs():
    uid   = int(get_jwt_identity())
    top_n = int(request.args.get("top_n",10))
    items = recommendation_engine.recommend_jobs(uid, top_n)
    Recommendation.query.filter_by(user_id=uid, rec_type="job").delete()
    for item in items:
        job = item["job"]
        db.session.add(Recommendation(user_id=uid, job_id=job.id, rec_type="job",
            title=job.title, description=f"{job.company} — {job.location}",
            url=job.source_url or f"/jobs/{job.id}",
            score=item["score"], reason=", ".join(item["reasons"])))
    db.session.commit()
    return jsonify({"recommendations": [
        {"job": i["job"].to_dict(), "score": i["score"], "reasons": i["reasons"]}
        for i in items]})

@rec_bp.get("/skills")
@jwt_required()
def suggest_skills():
    uid   = int(get_jwt_identity())
    top_n = int(request.args.get("top_n",5))
    return jsonify({"skills_to_learn": recommendation_engine.suggest_skills(uid, top_n)})
