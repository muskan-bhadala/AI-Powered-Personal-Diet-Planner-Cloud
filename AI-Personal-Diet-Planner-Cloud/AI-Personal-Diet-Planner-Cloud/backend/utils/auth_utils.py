"""
backend/utils/auth_utils.py

Password hashing + JWT helpers.
- Passwords are never stored in plain text (werkzeug's salted hash).
- JWTs are short-lived, signed tokens the frontend stores and sends back
  in the Authorization header on every request. This demonstrates
  stateless cloud authentication (no server-side session storage needed,
  which is important for horizontal scaling — see docs/scalability.md).
"""

import os
import jwt
import datetime
from functools import wraps
from flask import request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

JWT_SECRET = os.environ.get("JWT_SECRET", "dev-secret-change-me")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 12


def hash_password(plain_password: str) -> str:
    return generate_password_hash(plain_password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    return check_password_hash(password_hash, plain_password)


def create_token(user_id: str) -> str:
    payload = {
        "user_id": user_id,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=JWT_EXPIRY_HOURS),
        "iat": datetime.datetime.utcnow(),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str):
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])


def login_required(f):
    """
    Decorator that protects a route: extracts and verifies the JWT from
    the 'Authorization: Bearer <token>' header, then passes user_id into
    the wrapped view function as its first argument.
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid Authorization header"}), 401
        token = auth_header.split(" ", 1)[1]
        try:
            payload = decode_token(token)
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired, please log in again"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid authentication token"}), 401
        return f(payload["user_id"], *args, **kwargs)
    return wrapper
