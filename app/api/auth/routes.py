from flask import Blueprint, request, jsonify, redirect, current_app
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity,
)
from app.extensions import db, bcrypt
from app.models.models import User, Profile
from app.services.services import email_service, otp_service
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
import os

auth_bp = Blueprint("auth", __name__)


def _serializer():
    return URLSafeTimedSerializer(os.getenv("SECRET_KEY", "careeriq-secret-dev-2024"))


def _tokens(user):
    uid = str(user.id)
    return create_access_token(identity=uid), create_refresh_token(identity=uid)


@auth_bp.post("/register")
def register():
    d = request.get_json() or {}
    for f in ["email", "password", "full_name"]:
        if not d.get(f):
            return jsonify({"error": f"'{f}' is required."}), 400
    if len(d["password"]) < 6:
        return jsonify({"error": "Password must be at least 6 characters."}), 400

    if User.query.filter_by(email=d["email"].lower()).first():
        return jsonify({"error": "Email already registered."}), 409

    role = d.get("role", "user")
    if role not in ("user", "recruiter"):
        role = "user"

    hashed = bcrypt.generate_password_hash(d["password"]).decode("utf-8")
    user   = User(
        email=d["email"].lower().strip(),
        password_hash=hashed,
        full_name=d["full_name"].strip(),
        role=role,
    )
    db.session.add(user)
    db.session.flush()
    db.session.add(Profile(user_id=user.id))
    db.session.commit()

    token = email_service.make_token(user.email)
    er    = email_service.send_verification(user.email, user.full_name, token)
    at, rt = _tokens(user)

    resp = {
        "message": "Account created! Please verify your email.",
        "user": user.to_dict(),
        "access_token": at,
        "refresh_token": rt,
    }
    if er.get("dev_mode"):
        resp["dev_verify_url"] = er["verify_url"]
    return jsonify(resp), 201


@auth_bp.post("/login")
def login():
    d = request.get_json() or {}
    if not d.get("email") or not d.get("password"):
        return jsonify({"error": "Email and password required."}), 400

    user = User.query.filter_by(email=d["email"].lower()).first()
    if not user or not user.is_active:
        return jsonify({"error": "Invalid email or password."}), 401
    if not bcrypt.check_password_hash(user.password_hash, d["password"]):
        return jsonify({"error": "Invalid email or password."}), 401

    at, rt = _tokens(user)
    return jsonify({
        "message": "Login successful.",
        "user": user.to_dict(),
        "access_token": at,
        "refresh_token": rt,
    })


@auth_bp.post("/refresh")
@jwt_required(refresh=True)
def refresh():
    return jsonify({"access_token": create_access_token(identity=get_jwt_identity())})


@auth_bp.get("/me")
@jwt_required()
def me():
    user = User.query.get(int(get_jwt_identity()))
    if not user:
        return jsonify({"error": "Not found."}), 404
    return jsonify({
        "user": user.to_dict(),
        "completeness_score": user.completeness_score(),
        "completeness_tips":  user.completeness_tips(),
    })


@auth_bp.get("/verify-email/<token>")
def verify_email(token):
    s = _serializer()
    try:
        email = s.loads(token, salt="email-verify", max_age=3600)
    except SignatureExpired:
        return jsonify({"error": "Link expired."}), 400
    except BadSignature:
        return jsonify({"error": "Invalid link."}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found."}), 404
    user.email_verified = True
    db.session.commit()
    return redirect(current_app.config["APP_BASE_URL"] + "/dashboard?verified=1")


@auth_bp.post("/resend-verification")
@jwt_required()
def resend():
    user = User.query.get(int(get_jwt_identity()))
    if not user:
        return jsonify({"error": "Not found."}), 404
    if user.email_verified:
        return jsonify({"message": "Already verified."}), 200
    token = email_service.make_token(user.email)
    er    = email_service.send_verification(user.email, user.full_name, token)
    resp  = {"message": "Verification email sent."}
    if er.get("dev_mode"):
        resp["dev_verify_url"] = er["verify_url"]
    return jsonify(resp)


@auth_bp.post("/send-otp")
@jwt_required()
def send_otp():
    user  = User.query.get(int(get_jwt_identity()))
    phone = (request.get_json() or {}).get("phone_number", "").strip()
    if not phone:
        return jsonify({"error": "phone_number required."}), 400
    res  = otp_service.send_otp(user, phone)
    resp = {"message": f"OTP sent to {phone}."}
    if res.get("dev_mode"):
        resp["dev_otp"] = res["otp"]
    return jsonify(resp)


@auth_bp.post("/verify-otp")
@jwt_required()
def verify_otp():
    user = User.query.get(int(get_jwt_identity()))
    otp  = (request.get_json() or {}).get("otp", "").strip()
    if not otp:
        return jsonify({"error": "otp required."}), 400
    res = otp_service.verify_otp(user, otp)
    if not res["success"]:
        return jsonify({"error": res["error"]}), 400
    return jsonify({"message": "Phone verified!"})


@auth_bp.post("/change-password")
@jwt_required()
def change_pw():
    user = User.query.get(int(get_jwt_identity()))
    d    = request.get_json() or {}
    old, new = d.get("old_password", ""), d.get("new_password", "")
    if not bcrypt.check_password_hash(user.password_hash, old):
        return jsonify({"error": "Current password is incorrect."}), 400
    if len(new) < 6:
        return jsonify({"error": "New password too short."}), 400
    user.password_hash = bcrypt.generate_password_hash(new).decode("utf-8")
    db.session.commit()
    return jsonify({"message": "Password updated."})
