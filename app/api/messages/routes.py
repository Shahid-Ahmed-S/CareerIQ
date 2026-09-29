from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models.models import Message, User, Connection
from sqlalchemy import or_, and_

messages_bp = Blueprint("messages", __name__)

def are_connected(uid1, uid2):
    return Connection.query.filter(
        Connection.status=="accepted",
        or_(and_(Connection.sender_id==uid1,Connection.receiver_id==uid2),
            and_(Connection.sender_id==uid2,Connection.receiver_id==uid1))
    ).first() is not None

@messages_bp.get("/threads")
@jwt_required()
def threads():
    uid = int(get_jwt_identity())
    msgs = Message.query.filter(
        or_(Message.sender_id==uid, Message.receiver_id==uid)
    ).order_by(Message.created_at.desc()).all()
    seen, result = set(), []
    for m in msgs:
        other = m.receiver_id if m.sender_id==uid else m.sender_id
        if other not in seen:
            seen.add(other)
            u = User.query.get(other)
            unread = Message.query.filter_by(sender_id=other,receiver_id=uid,is_read=False).count()
            result.append({"user_id":other,
                           "full_name":u.full_name if u else "Unknown",
                           "avatar":(u.full_name or "?")[0].upper() if u else "?",
                           "avatar_url": u.avatar_url if u else None,
                           "headline":u.profile.headline if u and u.profile else "",
                           "last_message":m.content[:60],
                           "last_time":m.created_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
                           "unread":unread})
    return jsonify({"threads":result})

@messages_bp.get("/<int:other_id>")
@jwt_required()
def conversation(other_id):
    uid = int(get_jwt_identity())
    msgs = Message.query.filter(
        or_(and_(Message.sender_id==uid,Message.receiver_id==other_id),
            and_(Message.sender_id==other_id,Message.receiver_id==uid))
    ).order_by(Message.created_at.asc()).all()
    for m in msgs:
        if m.receiver_id==uid and not m.is_read:
            m.is_read = True
    db.session.commit()
    return jsonify({"messages":[m.to_dict(current_user_id=uid) for m in msgs]})

@messages_bp.post("/<int:other_id>")
@jwt_required()
def send_message(other_id):
    uid  = int(get_jwt_identity())
    if not User.query.get(other_id): return jsonify({"error":"User not found."}), 404
    text = (request.get_json() or {}).get("content","").strip()
    if not text: return jsonify({"error":"Message empty."}), 400
    if len(text) > 2000: return jsonify({"error":"Too long."}), 400
    m = Message(sender_id=uid,receiver_id=other_id,content=text)
    db.session.add(m); db.session.commit()
    return jsonify({"message":"Sent.","msg":m.to_dict(current_user_id=uid)}), 201

@messages_bp.get("/unread-count")
@jwt_required()
def unread_count():
    uid = int(get_jwt_identity())
    n   = Message.query.filter_by(receiver_id=uid,is_read=False).count()
    return jsonify({"unread":n})
