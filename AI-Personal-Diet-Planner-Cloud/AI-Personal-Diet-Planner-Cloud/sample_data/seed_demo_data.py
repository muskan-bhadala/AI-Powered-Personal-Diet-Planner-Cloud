"""
sample_data/seed_demo_data.py

Registers the synthetic demo users from demo_users.json against a running
backend, sets their profiles, and generates one sample plan each — useful
for quickly populating the app before taking screenshots.

Usage (with the backend already running on port 5000):
    python sample_data/seed_demo_data.py
"""

import json
import os
import requests

BASE_URL = os.environ.get("APP_BASE_URL", "http://localhost:5000")

with open(os.path.join(os.path.dirname(__file__), "demo_users.json")) as f:
    USERS = json.load(f)

for u in USERS:
    r = requests.post(f"{BASE_URL}/api/register", json={
        "name": u["name"], "email": u["email"], "password": u["password"]
    })
    if r.status_code not in (201, 409):
        print(f"[skip] {u['email']}: {r.status_code} {r.text}")
        continue

    if r.status_code == 409:
        r = requests.post(f"{BASE_URL}/api/login", json={
            "email": u["email"], "password": u["password"]
        })

    token = r.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    requests.put(f"{BASE_URL}/api/profile", headers=headers, json={
        "age": u["age"], "height_cm": u["height_cm"], "weight_kg": u["weight_kg"],
        "activity_level": u["activity_level"], "dietary_preference": u["dietary_preference"],
        "goal": u["goal"], "allergies": u["allergies"],
    })

    plan_resp = requests.post(f"{BASE_URL}/api/generate-plan", headers=headers, json={})
    print(f"[ok] {u['email']} -> plan generated ({plan_resp.json().get('source')})")

print("Demo data seeding complete.")
