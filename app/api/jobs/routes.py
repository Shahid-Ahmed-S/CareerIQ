from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.services import JobService

jobs_bp = Blueprint("jobs", __name__)

@jobs_bp.get("/")
@jwt_required()
def list_jobs():
    filters = {}
    for k in ["title","location","job_type","experience_level"]:
        v = request.args.get(k)
        if v: filters[k] = v
    try: page, pp = int(request.args.get("page",1)), int(request.args.get("per_page",12))
    except: page, pp = 1, 12
    pag = JobService.list_jobs(filters, page, pp)
    return jsonify({"jobs": [j.to_dict() for j in pag.items],
                    "total": pag.total, "page": pag.page,
                    "pages": pag.pages, "has_next": pag.has_next})

@jobs_bp.get("/<int:jid>")
@jwt_required()
def get_job(jid):
    job = JobService.get(jid)
    if not job: return jsonify({"error": "Not found."}), 404
    return jsonify({"job": job.to_dict()})

@jobs_bp.post("/")
@jwt_required()
def create_job():
    d = request.get_json() or {}
    if not d.get("title"): return jsonify({"error": "title required."}), 400
    res = JobService.create(d, posted_by=int(get_jwt_identity()))
    return jsonify({"message": "Job created.", "job": res["job"].to_dict()}), 201
