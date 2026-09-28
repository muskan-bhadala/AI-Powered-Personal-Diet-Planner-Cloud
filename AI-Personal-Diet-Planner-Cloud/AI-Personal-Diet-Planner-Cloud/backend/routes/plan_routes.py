"""
backend/routes/plan_routes.py
POST   /api/generate-plan  -> run the AI engine and save the resulting plan
GET    /api/plans          -> list all plans for the logged-in user only
GET    /api/plans/<id>     -> fetch one plan (must belong to this user)
DELETE /api/plans/<id>     -> delete one plan (must belong to this user)
"""

from flask import Blueprint, request, jsonify
from cloud import database_service as db
from backend.utils.auth_utils import login_required
from ai_engine.diet_engine import generate_plan

plan_bp = Blueprint("plans", __name__)


@plan_bp.route("/api/generate-plan", methods=["POST"])
@login_required
def generate_plan_route(user_id):
    user = db.get_user_by_id(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json(silent=True) or {}
    # Allow overriding profile values for this one generation (optional),
    # otherwise fall back to what's stored on the profile.
    preference = data.get("dietary_preference") or user.get("dietary_preference") or "vegetarian"
    activity_level = data.get("activity_level") or user.get("activity_level") or "moderate"
    goal = data.get("goal") or user.get("goal") or "general balanced eating"
    allergies = data.get("allergies") or user.get("allergies") or ""

    plan, source = generate_plan(preference, activity_level, goal, allergies)
    plan_id = db.save_diet_plan(user_id, plan, source)

    return jsonify({
        "message": "Diet plan generated",
        "plan_id": plan_id,
        "source": source,  # "ai_api" or "rule_based" (fallback)
        "plan": plan,
    }), 201


@plan_bp.route("/api/plans", methods=["GET"])
@login_required
def list_plans(user_id):
    plans = db.list_plans_for_user(user_id)
    return jsonify({"plans": plans}), 200


@plan_bp.route("/api/plans/<plan_id>", methods=["GET"])
@login_required
def get_plan_route(user_id, plan_id):
    plan = db.get_plan(plan_id, user_id)
    if not plan:
        return jsonify({"error": "Plan not found"}), 404
    return jsonify({"plan": plan}), 200


@plan_bp.route("/api/plans/<plan_id>", methods=["DELETE"])
@login_required
def delete_plan_route(user_id, plan_id):
    deleted = db.delete_plan(plan_id, user_id)
    if not deleted:
        return jsonify({"error": "Plan not found"}), 404
    return jsonify({"message": "Plan deleted"}), 200
