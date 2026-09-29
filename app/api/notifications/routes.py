from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models.models import Notification

notif_bp = Blueprint("notifications", __name__)


def create_notification(user_id, actor_id, notif_type, title, body, link=""):
    """Helper to create and save a notification."""
    if user_id == actor_id:
        return  # Don't notify yourself
    n = Notification(user_id=user_id, actor_id=actor_id,
                     notif_type=notif_type, title=title, body=body, link=link)
    db.session.add(n)
    db.session.commit()

    # Emit real-time notification via SocketIO
    try:
        from app.extensions import socketio
        socketio.emit("notification", n.to_dict(), room=f"user_{user_id}")
    except Exception:
        pass
    return n


@notif_bp.get("/")
@jwt_required()
def list_notifications():
    uid  = int(get_jwt_identity())
    page = int(request.args.get("page", 1))
    notifs = (Notification.query
              .filter_by(user_id=uid)
              .order_by(Notification.created_at.desc())
              .paginate(page=page, per_page=20, error_out=False))
    return jsonify({
        "notifications": [n.to_dict() for n in notifs.items],
        "unread_count":  Notification.query.filter_by(user_id=uid, is_read=False).count(),
        "has_next":      notifs.has_next,
    })


@notif_bp.post("/mark-read")
@jwt_required()
def mark_read():
    uid = int(get_jwt_identity())
    nid = (request.get_json() or {}).get("notification_id")
    if nid:
        n = Notification.query.filter_by(id=nid, user_id=uid).first()
        if n: n.is_read = True
    else:
        Notification.query.filter_by(user_id=uid, is_read=False).update({"is_read": True})
    db.session.commit()
    return jsonify({"message": "Marked as read."})


@notif_bp.get("/unread-count")
@jwt_required()
def unread_count():
    uid = int(get_jwt_identity())
    return jsonify({"count": Notification.query.filter_by(user_id=uid, is_read=False).count()})
