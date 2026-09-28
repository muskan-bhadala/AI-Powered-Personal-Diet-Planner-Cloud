"""
ai_engine/diet_engine.py

AI DIET RECOMMENDATION ENGINE
------------------------------
IMPORTANT DISCLAIMER (shown to users in the frontend too):
This engine produces a general wellness / educational example meal plan.
It is NOT medical or clinical nutrition advice, and does not diagnose or
treat any condition. Users should consult a qualified professional for
real dietary or medical decisions. All demo data is synthetic.

VERSION A — Rule-based engine (always available, no API key needed)
VERSION B — Optional external AI API call, used only if:
    - USE_AI_API=true in the environment, AND
    - an API key is configured
  If the API call fails or is disabled, the code automatically falls
  back to Version A so the project always stays fully executable without
  any paid service. This fallback pattern is a real cloud-architecture
  concept: "graceful degradation".
"""

import os
import json
import random

_FOOD_DATA_PATH = os.path.join(os.path.dirname(__file__), "food_data.json")
with open(_FOOD_DATA_PATH, "r") as f:
    FOOD_DATA = json.load(f)

DISCLAIMER = (
    "This is an educational, general-wellness example meal plan generated "
    "from synthetic demo data. It is not medical or clinical nutrition advice."
)

HYDRATION_REMINDERS = [
    "Remember to drink water regularly throughout the day.",
    "Aim to stay hydrated — keep a water bottle within reach today.",
    "Don't forget fluids: water, herbal tea, or infused water all count.",
]


def _normalize_preference(pref: str) -> str:
    pref = (pref or "").strip().lower().replace(" ", "_")
    if pref in ("vegetarian", "veg"):
        return "vegetarian"
    if pref in ("vegan",):
        return "vegan"
    return "non_vegetarian"


def _goal_multiplier(goal: str) -> float:
    goal = (goal or "").strip().lower()
    if "weight-management" in goal or "weight_management" in goal or "loss" in goal:
        return 0.85
    if "fitness" in goal or "gain" in goal:
        return 1.15
    return 1.0  # general balanced eating


def generate_plan_rule_based(preference: str, activity_level: str, goal: str) -> dict:
    """VERSION A — deterministic-ish rule-based recommendation."""
    pref_key = _normalize_preference(preference)
    data = FOOD_DATA.get(pref_key, FOOD_DATA["vegetarian"])
    multiplier = _goal_multiplier(goal)

    def pick(meal):
        return random.choice(data[meal])

    breakfast = pick("breakfast")
    lunch = pick("lunch")
    snack = pick("snack")
    dinner = pick("dinner")

    total_calories = round(
        (breakfast["calories"] + lunch["calories"] + snack["calories"] + dinner["calories"])
        * multiplier
    )

    return {
        "breakfast": breakfast["item"],
        "lunch": lunch["item"],
        "snack": snack["item"],
        "dinner": dinner["item"],
        "nutrition_summary": (
            f"Approx. {total_calories} kcal today ({pref_key.replace('_', '-')} plan, "
            f"activity level: {activity_level or 'not specified'}). {DISCLAIMER}"
        ),
        "hydration_reminder": random.choice(HYDRATION_REMINDERS),
    }


def _call_external_ai_api(preference, activity_level, goal, allergies):
    """
    VERSION B — Optional call to an external AI API (e.g. Anthropic/OpenAI).
    Only attempted if USE_AI_API=true and an API key is present. Any error
    (network, auth, parsing) raises, and the caller falls back to Version A.
    """
    if os.environ.get("USE_AI_API", "false").lower() != "true":
        raise RuntimeError("AI API disabled via USE_AI_API env var")

    api_key = os.environ.get("AI_API_KEY")
    if not api_key:
        raise RuntimeError("AI_API_KEY not configured")

    import requests  # imported lazily so it's optional when unused

    prompt = (
        f"Create a one-day educational example meal plan (breakfast, lunch, "
        f"snack, dinner) for a {preference} diet, activity level {activity_level}, "
        f"goal {goal}, avoiding: {allergies or 'none specified'}. "
        f"Respond ONLY as JSON with keys breakfast, lunch, snack, dinner, "
        f"nutrition_summary. This is a general wellness example, not medical advice."
    )

    response = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": "claude-sonnet-4-6",
            "max_tokens": 500,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=10,
    )
    response.raise_for_status()
    data = response.json()
    text = "".join(block.get("text", "") for block in data.get("content", []))
    text = text.strip().removeprefix("```json").removesuffix("```").strip()
    parsed = json.loads(text)

    required = {"breakfast", "lunch", "snack", "dinner", "nutrition_summary"}
    if not required.issubset(parsed.keys()):
        raise ValueError("AI response missing required fields")

    parsed["nutrition_summary"] = f"{parsed['nutrition_summary']} {DISCLAIMER}"
    parsed["hydration_reminder"] = random.choice(HYDRATION_REMINDERS)
    return parsed


def generate_plan(preference: str, activity_level: str, goal: str, allergies: str = ""):
    """
    Public entry point used by the backend route.
    Tries the external AI API first (if enabled); falls back to the
    rule-based engine on ANY failure so the app never breaks.
    Returns (plan_dict, source) where source is "ai_api" or "rule_based".
    """
    try:
        plan = _call_external_ai_api(preference, activity_level, goal, allergies)
        return plan, "ai_api"
    except Exception:
        plan = generate_plan_rule_based(preference, activity_level, goal)
        return plan, "rule_based"
