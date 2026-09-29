"""
WebSocket event handlers — real-time messaging & notifications.
"""
from flask_socketio import join_room, leave_room, emit
from flask_jwt_extended import decode_token
from app.extensions import db
from app.models.models import Message, User


def register_events(socketio):

    @socketio.on("connect")
    def on_connect(auth):
        """Client connects — join their personal room."""
        try:
            token = (auth or {}).get("token", "")
            if not token:
                return False
            data = decode_token(token)
            uid  = int(data["sub"])
            join_room(f"user_{uid}")
            emit("connected", {"user_id": uid})
        except Exception:
            return False

    @socketio.on("disconnect")
    def on_disconnect():
        pass

    @socketio.on("join_conversation")
    def on_join_conversation(data):
        """Join a private conversation room between two users."""
        try:
            token = data.get("token", "")
            decoded = decode_token(token)
            uid   = int(decoded["sub"])
            other = int(data.get("other_id", 0))
            room  = f"conv_{min(uid, other)}_{max(uid, other)}"
            join_room(room)
            emit("joined_conversation", {"room": room})
        except Exception:
            pass

    @socketio.on("send_message")
    def on_send_message(data):
        """Send a message in real-time."""
        try:
            token   = data.get("token", "")
            decoded = decode_token(token)
            uid     = int(decoded["sub"])
            other   = int(data.get("receiver_id", 0))
            content = (data.get("content") or "").strip()

            if not content or not other:
                return

            msg = Message(sender_id=uid, receiver_id=other, content=content)
            db.session.add(msg)
            db.session.commit()

            msg_dict = msg.to_dict(current_user_id=uid)

            # Emit to the conversation room
            room = f"conv_{min(uid, other)}_{max(uid, other)}"
            emit("new_message", msg_dict, room=room)

            # Notify receiver
            sender = User.query.get(uid)
            try:
                from app.api.notifications.routes import create_notification
                create_notification(
                    user_id=other, actor_id=uid,
                    notif_type="message",
                    title=f"New message from {sender.full_name if sender else 'Someone'}",
                    body=content[:80],
                    link="/messages"
                )
            except Exception:
                pass

        except Exception as e:
            emit("error", {"message": str(e)})

    @socketio.on("typing")
    def on_typing(data):
        """Broadcast typing indicator."""
        try:
            token   = data.get("token", "")
            decoded = decode_token(token)
            uid     = int(decoded["sub"])
            other   = int(data.get("receiver_id", 0))
            room    = f"conv_{min(uid, other)}_{max(uid, other)}"
            emit("user_typing", {"user_id": uid, "is_typing": data.get("is_typing", False)},
                 room=room, include_self=False)
        except Exception:
            pass
