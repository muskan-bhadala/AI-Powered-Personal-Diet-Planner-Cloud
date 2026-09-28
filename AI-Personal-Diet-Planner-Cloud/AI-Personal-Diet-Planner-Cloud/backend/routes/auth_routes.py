"""
backend/routes/auth_routes.py
POST /api/register  -> create account (password hashed, never stored plain)
POST /api/login      -> verify credentials, return a signed JWT
POST /api/logout     -> stateless logout (frontend just deletes the token;
                         see docs/security.md for why this is normal for JWTs)
"""

import re
from flask import Blueprint, request, jsonify

from cloud import database_service as db
from backend.utils.auth_utils import hash_password, verify_password, create_token

auth_bp = Blueprint("auth", __name__)

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@auth_bp.route("/api/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not name or not email or not password:
        return jsonify({"error": "name, email and password are required"}), 400
    if not EMAIL_RE.match(email):
        return jsonify({"error": "Invalid email format"}), 400
    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters"}), 400

    if db.get_user_by_email(email):
        return jsonify({"error": "An account with this email already exists"}), 409

    user_id = db.create_user(name, email, hash_password(password))
    token = create_token(user_id)
    return jsonify({
        "message": "Registration successful",
        "token": token,
        "user": {"user_id": user_id, "name": name, "email": email},
    }), 201


@auth_bp.route("/api/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    user = db.get_user_by_email(email)
    if not user or not verify_password(password, user["password_hash"]):
        return jsonify({"error": "Invalid email or password"}), 401

    token = create_token(user["user_id"])
    return jsonify({
        "message": "Login successful",
        "token": token,
        "user": {"user_id": user["user_id"], "name": user["name"], "email": user["email"]},
    }), 200


@auth_bp.route("/api/logout", methods=["POST"])
def logout():
    # JWTs are stateless: "logging out" means the client discards the
    # token. There is no server-side session to destroy. This is normal
    # and expected for a JWT-based cloud API.
    return jsonify({"message": "Logged out. Please discard your token client-side."}), 200
