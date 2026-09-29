from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models.models import Connection, User, Profile, UserSkill

connections_bp = Blueprint("connections", __name__)

@connections_bp.get("/search")
@jwt_required()
def search():
    uid = int(get_jwt_identity())
    q   = request.args.get("q","").strip()
    if len(q) < 2: return jsonify({"users":[]})
    users = User.query.filter(
        User.full_name.ilike(f"%{q}%"),
        User.id != uid, User.is_active == True
    ).limit(20).all()
    result = []
    for u in users:
        conn = Connection.query.filter(
            ((Connection.sender_id==uid)&(Connection.receiver_id==u.id))|
            ((Connection.sender_id==u.id)&(Connection.receiver_id==uid))
        ).first()
        result.append({
            "id": u.id, "full_name": u.full_name,
            "avatar": u.full_name[0].upper(),
            "headline": u.profile.headline if u.profile else "",
            "location": u.profile.location if u.profile else "",
            "connection_status": conn.status if conn else None,
            "connection_id": conn.id if conn else None,
        })
    return jsonify({"users": result})

@connections_bp.post("/request/<int:uid>")
@jwt_required()
def send_request(uid):
    me = int(get_jwt_identity())
    if me == uid: return jsonify({"error":"Cannot connect with yourself."}), 400
    if not User.query.get(uid): return jsonify({"error":"User not found."}), 404
    ex = Connection.query.filter(
        ((Connection.sender_id==me)&(Connection.receiver_id==uid))|
        ((Connection.sender_id==uid)&(Connection.receiver_id==me))
    ).first()
    if ex: return jsonify({"error":"Request already exists."}), 409
    c = Connection(sender_id=me, receiver_id=uid)
    db.session.add(c); db.session.commit()
    try:
        from app.api.notifications.routes import create_notification
        sender = User.query.get(me)
        create_notification(
            user_id=uid, actor_id=me,
            notif_type="connection_request",
            title=f"{sender.full_name if sender else 'Someone'} sent you a connection request",
            body="Accept to connect and start messaging",
            link="/connections"
        )
    except Exception: pass
    return jsonify({"message":"Request sent.","connection":c.to_dict(me)}), 201

@connections_bp.post("/<int:cid>/accept")
@jwt_required()
def accept(cid):
    uid = int(get_jwt_identity())
    c   = Connection.query.filter_by(id=cid,receiver_id=uid,status="pending").first()
    if not c: return jsonify({"error":"Not found."}), 404
    c.status = "accepted"; db.session.commit()
    try:
        from app.api.notifications.routes import create_notification
        accepter = User.query.get(uid)
        create_notification(
            user_id=c.sender_id, actor_id=uid,
            notif_type="connection_accepted",
            title=f"{accepter.full_name if accepter else 'Someone'} accepted your connection request",
            body="You are now connected",
            link="/connections"
        )
    except Exception: pass
    return jsonify({"message":"Connected!","connection":c.to_dict(uid)})

@connections_bp.post("/<int:cid>/reject")
@jwt_required()
def reject(cid):
    uid = int(get_jwt_identity())
    c   = Connection.query.filter_by(id=cid,receiver_id=uid,status="pending").first()
    if not c: return jsonify({"error":"Not found."}), 404
    db.session.delete(c); db.session.commit()
    return jsonify({"message":"Request declined."})

@connections_bp.get("/")
@jwt_required()
def my_connections():
    uid  = int(get_jwt_identity())
    cons = Connection.query.filter(
        ((Connection.sender_id==uid)|(Connection.receiver_id==uid)),
        Connection.status=="accepted"
    ).all()
    return jsonify({"connections":[c.to_dict(uid) for c in cons]})

@connections_bp.get("/pending")
@jwt_required()
def pending():
    uid  = int(get_jwt_identity())
    reqs = Connection.query.filter_by(receiver_id=uid,status="pending").all()
    return jsonify({"pending":[r.to_dict(uid) for r in reqs]})

@connections_bp.delete("/<int:cid>")
@jwt_required()
def remove(cid):
    uid = int(get_jwt_identity())
    c   = Connection.query.filter(
        Connection.id==cid,
        (Connection.sender_id==uid)|(Connection.receiver_id==uid)
    ).first()
    if not c: return jsonify({"error":"Not found."}), 404
    db.session.delete(c); db.session.commit()
    return jsonify({"message":"Connection removed."})
