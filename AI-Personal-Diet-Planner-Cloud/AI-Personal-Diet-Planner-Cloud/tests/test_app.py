"""
tests/test_app.py

Automated tests covering the core test plan from docs/testing.md.
Run with:  pytest  (from the project root, with dependencies installed)

Each test uses a fresh temporary SQLite DB and storage bucket so tests
never touch real project data.
"""

import os
import sys
import io
import tempfile
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)


@pytest.fixture()
def client(monkeypatch):
    db_fd, db_path = tempfile.mkstemp(suffix=".sqlite3")
    storage_dir = tempfile.mkdtemp()
    monkeypatch.setenv("DATABASE_PATH", db_path)
    monkeypatch.setenv("STORAGE_BUCKET_PATH", storage_dir)
    monkeypatch.setenv("JWT_SECRET", "test-secret")
    monkeypatch.setenv("USE_AI_API", "false")

    # Re-import modules fresh so they pick up the patched env vars.
    for mod in list(sys.modules):
        if mod.startswith(("cloud.", "ai_engine.", "backend.")) or mod in ("cloud", "backend"):
            del sys.modules[mod]

    from cloud import database_service as db
    db.init_db()

    from backend.app import app as flask_app
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c

    os.close(db_fd)
    os.remove(db_path)


def register(client, email="user@example.com", password="password123", name="Demo User"):
    return client.post("/api/register", json={"name": name, "email": email, "password": password})


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# T01 / T02 — Registration
# ---------------------------------------------------------------------------

def test_new_user_registration(client):
    resp = register(client)
    assert resp.status_code == 201
    assert "token" in resp.get_json()


def test_existing_email_registration_rejected(client):
    register(client)
    resp = register(client)
    assert resp.status_code == 409


# ---------------------------------------------------------------------------
# T03 / T04 — Login
# ---------------------------------------------------------------------------

def test_valid_login(client):
    register(client)
    resp = client.post("/api/login", json={"email": "user@example.com", "password": "password123"})
    assert resp.status_code == 200
    assert "token" in resp.get_json()


def test_invalid_login(client):
    register(client)
    resp = client.post("/api/login", json={"email": "user@example.com", "password": "wrongpass"})
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# T05 — Unauthorized dashboard/profile access
# ---------------------------------------------------------------------------

def test_unauthorized_profile_access(client):
    resp = client.get("/api/profile")
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# T06 — Profile creation/update
# ---------------------------------------------------------------------------

def test_profile_update(client):
    token = register(client).get_json()["token"]
    resp = client.put("/api/profile", headers=auth_headers(token), json={
        "dietary_preference": "vegan", "goal": "fitness-oriented demo", "activity_level": "active"
    })
    assert resp.status_code == 200
    assert resp.get_json()["profile"]["dietary_preference"] == "vegan"


# ---------------------------------------------------------------------------
# T07-T10 — Diet plan generation for each preference/goal
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("preference", ["vegetarian", "vegan", "non_vegetarian"])
def test_generate_plan_for_each_preference(client, preference):
    token = register(client).get_json()["token"]
    resp = client.post("/api/generate-plan", headers=auth_headers(token),
                        json={"dietary_preference": preference})
    assert resp.status_code == 201
    body = resp.get_json()
    for meal in ("breakfast", "lunch", "snack", "dinner"):
        assert body["plan"][meal]


def test_generate_plan_different_goal(client):
    token = register(client).get_json()["token"]
    resp = client.post("/api/generate-plan", headers=auth_headers(token),
                        json={"goal": "weight-management demo"})
    assert resp.status_code == 201


# ---------------------------------------------------------------------------
# T11 / T12 — AI API failure -> rule-based fallback
# ---------------------------------------------------------------------------

def test_ai_api_disabled_falls_back_to_rule_based(client, monkeypatch):
    monkeypatch.setenv("USE_AI_API", "false")
    token = register(client).get_json()["token"]
    resp = client.post("/api/generate-plan", headers=auth_headers(token), json={})
    assert resp.status_code == 201
    assert resp.get_json()["source"] == "rule_based"


# ---------------------------------------------------------------------------
# T13 / T14 — Save & retrieve plan
# ---------------------------------------------------------------------------

def test_save_and_retrieve_plan(client):
    token = register(client).get_json()["token"]
    gen = client.post("/api/generate-plan", headers=auth_headers(token), json={})
    plan_id = gen.get_json()["plan_id"]

    resp = client.get(f"/api/plans/{plan_id}", headers=auth_headers(token))
    assert resp.status_code == 200
    assert resp.get_json()["plan"]["plan_id"] == plan_id


# ---------------------------------------------------------------------------
# T15 / T16 / T17 — Upload / retrieve / invalid file
# ---------------------------------------------------------------------------

def test_upload_and_retrieve_file(client):
    token = register(client).get_json()["token"]
    data = {"file": (io.BytesIO(b"hello world"), "note.txt")}
    resp = client.post("/api/upload", headers=auth_headers(token), data=data,
                        content_type="multipart/form-data")
    assert resp.status_code == 201
    file_id = resp.get_json()["file_id"]

    download = client.get(f"/api/files/{file_id}", headers=auth_headers(token))
    assert download.status_code == 200
    assert download.data == b"hello world"


def test_invalid_file_type_rejected(client):
    token = register(client).get_json()["token"]
    data = {"file": (io.BytesIO(b"fake exe"), "virus.exe")}
    resp = client.post("/api/upload", headers=auth_headers(token), data=data,
                        content_type="multipart/form-data")
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# T18 — User isolation: User A cannot access User B's data
# ---------------------------------------------------------------------------

def test_user_isolation_on_plans_and_files(client):
    token_a = register(client, email="a@example.com").get_json()["token"]
    token_b = register(client, email="b@example.com").get_json()["token"]

    gen = client.post("/api/generate-plan", headers=auth_headers(token_a), json={})
    plan_id = gen.get_json()["plan_id"]

    # User B tries to fetch User A's plan.
    resp = client.get(f"/api/plans/{plan_id}", headers=auth_headers(token_b))
    assert resp.status_code == 404

    # Same isolation check for files.
    data = {"file": (io.BytesIO(b"secret"), "secret.txt")}
    upload = client.post("/api/upload", headers=auth_headers(token_a), data=data,
                          content_type="multipart/form-data")
    file_id = upload.get_json()["file_id"]
    resp = client.get(f"/api/files/{file_id}", headers=auth_headers(token_b))
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# T19 — Logout
# ---------------------------------------------------------------------------

def test_logout(client):
    resp = client.post("/api/logout")
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# T20 — Health check (used for monitoring / cloud/db failure visibility)
# ---------------------------------------------------------------------------

def test_health_check(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "ok"
