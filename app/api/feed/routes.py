from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models.models import Post, PostLike, PostComment

feed_bp = Blueprint("feed", __name__)

@feed_bp.get("/")
@jwt_required()
def get_feed():
    uid  = int(get_jwt_identity())
    page = int(request.args.get("page",1))
    ptype= request.args.get("type")
    q    = Post.query.filter_by(is_deleted=False)
    if ptype: q = q.filter_by(post_type=ptype)
    pag  = q.order_by(Post.created_at.desc()).paginate(page=page,per_page=15,error_out=False)
    return jsonify({"posts":[p.to_dict(current_user_id=uid) for p in pag.items],
                    "has_next":pag.has_next,"total":pag.total})

@feed_bp.post("/")
@jwt_required()
def create_post():
    uid  = int(get_jwt_identity())
    d    = request.get_json() or {}
    text = (d.get("content") or "").strip()
    if not text: return jsonify({"error": "Content required."}), 400
    if len(text) > 3000: return jsonify({"error": "Too long (max 3000 chars)."}), 400
    ptype = d.get("post_type","post")
    if ptype not in ("post","achievement","milestone","certification","job_update","project"):
        ptype = "post"
    p = Post(user_id=uid, content=text, post_type=ptype,
             achievement_title=(d.get("achievement_title") or "").strip() or None,
             achievement_icon=d.get("achievement_icon","🏆"),
             media_url=d.get("media_url") or None,
             media_type=d.get("media_type") or None)
    db.session.add(p); db.session.commit()
    return jsonify({"message":"Posted.","post":p.to_dict(current_user_id=uid)}), 201

@feed_bp.delete("/<int:pid>")
@jwt_required()
def delete_post(pid):
    uid = int(get_jwt_identity())
    p   = Post.query.filter_by(id=pid,is_deleted=False).first()
    if not p: return jsonify({"error":"Not found."}), 404
    if p.user_id != uid: return jsonify({"error":"Not your post."}), 403
    p.is_deleted = True; db.session.commit()
    return jsonify({"message":"Deleted."})

@feed_bp.patch("/<int:pid>")
@jwt_required()
def edit_post(pid):
    uid = int(get_jwt_identity())
    p   = Post.query.filter_by(id=pid, is_deleted=False).first()
    if not p: return jsonify({"error":"Not found."}), 404
    if p.user_id != uid: return jsonify({"error":"Not your post."}), 403
    text = (request.get_json() or {}).get("content","").strip()
    if not text: return jsonify({"error":"Content required."}), 400
    p.content = text
    db.session.commit()
    return jsonify({"message":"Updated.","post":p.to_dict(current_user_id=uid)})


@feed_bp.post("/<int:pid>/like")
@jwt_required()
def toggle_like(pid):
    uid = int(get_jwt_identity())
    p   = Post.query.filter_by(id=pid,is_deleted=False).first()
    if not p: return jsonify({"error":"Not found."}), 404
    ex  = PostLike.query.filter_by(post_id=pid,user_id=uid).first()
    if ex:
        db.session.delete(ex); liked = False
    else:
        db.session.add(PostLike(post_id=pid,user_id=uid)); liked = True
    db.session.commit()
    return jsonify({"liked":liked,"like_count":p.like_count()})

@feed_bp.get("/<int:pid>/comments")
@jwt_required()
def get_comments(pid):
    p = Post.query.filter_by(id=pid,is_deleted=False).first()
    if not p: return jsonify({"error":"Not found."}), 404
    cs = PostComment.query.filter_by(post_id=pid,is_deleted=False).order_by(PostComment.created_at).all()
    return jsonify({"comments":[c.to_dict() for c in cs]})

@feed_bp.post("/<int:pid>/comments")
@jwt_required()
def add_comment(pid):
    uid  = int(get_jwt_identity())
    p    = Post.query.filter_by(id=pid,is_deleted=False).first()
    if not p: return jsonify({"error":"Not found."}), 404
    text = (request.get_json() or {}).get("content","").strip()
    if not text: return jsonify({"error":"Comment empty."}), 400
    c = PostComment(post_id=pid,user_id=uid,content=text)
    db.session.add(c); db.session.commit()
    # Notify post author
    if p.user_id != uid:
        try:
            from app.api.notifications.routes import create_notification
            commenter = User.query.get(uid)
            create_notification(
                user_id=p.user_id, actor_id=uid,
                notif_type="comment",
                title=f"{commenter.full_name if commenter else 'Someone'} commented on your post",
                body=content[:60],
                link="/feed"
            )
        except Exception: pass
    return jsonify({"message":"Added.","comment":c.to_dict()}), 201

@feed_bp.delete("/<int:pid>/comments/<int:cid>")
@jwt_required()
def del_comment(pid,cid):
    uid = int(get_jwt_identity())
    c   = PostComment.query.filter_by(id=cid,post_id=pid,is_deleted=False).first()
    if not c: return jsonify({"error":"Not found."}), 404
    if c.user_id != uid: return jsonify({"error":"Not yours."}), 403
    c.is_deleted = True; db.session.commit()
    return jsonify({"message":"Deleted."})


@feed_bp.post("/upload-media")
@jwt_required()
def upload_media():
    import os, uuid
    from flask import current_app
    uid = int(get_jwt_identity())

    if "file" not in request.files:
        return jsonify({"error": "No file uploaded."}), 400

    file = request.files["file"]
    if not file.filename:
        return jsonify({"error": "No file selected."}), 400

    ext = file.filename.rsplit(".", 1)[-1].lower()

    IMAGE_EXTS = {"jpg", "jpeg", "png", "gif", "webp"}
    VIDEO_EXTS = {"mp4", "mov", "avi", "webm", "mkv"}

    if ext in IMAGE_EXTS:
        media_type = "image"
    elif ext in VIDEO_EXTS:
        media_type = "video"
    else:
        return jsonify({"error": "Unsupported file type. Use JPG, PNG, GIF, MP4, MOV or WEBM."}), 400

    # Use Flask static folder directly — guaranteed correct path
    upload_dir = os.path.join(current_app.static_folder, "uploads", "posts")
    os.makedirs(upload_dir, exist_ok=True)

    filename  = f"post_{uid}_{uuid.uuid4().hex[:8]}.{ext}"
    save_path = os.path.join(upload_dir, filename)
    file.save(save_path)

    media_url = f"/static/uploads/posts/{filename}"
    return jsonify({"media_url": media_url, "media_type": media_type}), 200
