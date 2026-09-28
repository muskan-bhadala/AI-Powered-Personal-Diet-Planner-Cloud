"""
backend/routes/profile_routes.py
GET /api/profile  -> return the logged-in user's profile (protected)
PUT /api/profile  -> update demo profile fields (protected)
"""

from flask import Blueprint, request, jsonify
from cloud import database_service as db
from backend.utils.auth_utils import login_required

profile_bp = Blueprint("profile", __name__)


def _public_profile(user: dict) -> dict:
    return {
        "user_id": user["user_id"],
        "name": user["name"],
        "email": user["email"],
        "age": user.get("age"),
        "height_cm": user.get("height_cm"),
        "weight_kg": user.get("weight_kg"),
        "activity_level": user.get("activity_level"),
        "dietary_preference": user.get("dietary_preference"),
        "goal": user.get("goal"),
        "allergies": user.get("allergies"),
    }


@profile_bp.route("/api/profile", methods=["GET"])
@login_required
def get_profile(user_id):
    user = db.get_user_by_id(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify(_public_profile(user)), 200


@profile_bp.route("/api/profile", methods=["PUT"])
@login_required
def update_profile(user_id):
    data = request.get_json(silent=True) or {}
    # NOTE: demo/educational fields only — never used for medical diagnosis.
    allowed_fields = ("name", "age", "height_cm", "weight_kg", "activity_level",
                       "dietary_preference", "goal", "allergies")
    updates = {k: data[k] for k in allowed_fields if k in data}

    if "activity_level" in updates and updates["activity_level"] not in (
        "sedentary", "light", "moderate", "active", None, ""
    ):
        return jsonify({"error": "Invalid activity_level"}), 400
    if "dietary_preference" in updates and updates["dietary_preference"] not in (
        "vegetarian", "vegan", "non_vegetarian", None, ""
    ):
        return jsonify({"error": "Invalid dietary_preference"}), 400

    db.update_user_profile(user_id, updates)
    user = db.get_user_by_id(user_id)
    return jsonify({"message": "Profile updated", "profile": _public_profile(user)}), 200
