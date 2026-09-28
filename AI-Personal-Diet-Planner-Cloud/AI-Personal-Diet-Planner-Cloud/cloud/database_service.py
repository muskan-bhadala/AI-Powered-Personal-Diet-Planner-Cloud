"""
cloud/database_service.py

CLOUD DATABASE SERVICE
-----------------------
This module simulates a managed cloud database (e.g. Firestore / Supabase /
Amazon RDS) using local SQLite so the whole project runs for free with no
external account required.

WHY THIS DESIGN:
    - All database access goes through the functions in this one file.
    - To move to a real cloud database later, you only need to rewrite the
      functions below (e.g. swap sqlite3 calls for Firestore SDK calls).
      Nothing in routes/ or services/ needs to change, because they only
      ever call db.something(...), never sqlite3 directly.
    - This is the same pattern ("repository pattern") used in real
      industry backends to keep cloud providers swappable.

Tables (collections in a NoSQL equivalent):
    users        -> USERS collection
    diet_plans   -> DIET_PLANS collection
    user_files   -> USER_FILES collection
"""

import sqlite3
import os
import uuid
from datetime import datetime, timezone
from contextlib import contextmanager

# In a real cloud deployment this path would instead be a connection string
# read from an environment variable, e.g. os.environ["DATABASE_URL"].
DB_PATH = os.environ.get("DATABASE_PATH", os.path.join(os.path.dirname(__file__), "..", "cloud_db.sqlite3"))


def _now():
    return datetime.now(timezone.utc).isoformat()


def new_id():
    return str(uuid.uuid4())


@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    """Creates tables if they do not exist yet. Called once on app startup."""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                age INTEGER,
                height_cm REAL,
                weight_kg REAL,
                activity_level TEXT,
                dietary_preference TEXT,
                goal TEXT,
                allergies TEXT,
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS diet_plans (
                plan_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                breakfast TEXT,
                lunch TEXT,
                snack TEXT,
                dinner TEXT,
                nutrition_summary TEXT,
                hydration_reminder TEXT,
                source TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_files (
                file_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                filename TEXT NOT NULL,
                storage_path TEXT NOT NULL,
                content_type TEXT,
                uploaded_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)


# ---------------------------------------------------------------------------
# USERS
# ---------------------------------------------------------------------------

def create_user(name, email, password_hash):
    user_id = new_id()
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO users (user_id, name, email, password_hash, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (user_id, name, email, password_hash, _now()),
        )
    return user_id


def get_user_by_email(email):
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        return dict(row) if row else None


def get_user_by_id(user_id):
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
        return dict(row) if row else None


def update_user_profile(user_id, fields: dict):
    if not fields:
        return
    allowed = {"name", "age", "height_cm", "weight_kg", "activity_level",
               "dietary_preference", "goal", "allergies"}
    fields = {k: v for k, v in fields.items() if k in allowed}
    if not fields:
        return
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [user_id]
    with get_connection() as conn:
        conn.execute(f"UPDATE users SET {set_clause} WHERE user_id = ?", values)


# ---------------------------------------------------------------------------
# DIET PLANS
# ---------------------------------------------------------------------------

def save_diet_plan(user_id, plan: dict, source: str):
    plan_id = new_id()
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO diet_plans
               (plan_id, user_id, breakfast, lunch, snack, dinner,
                nutrition_summary, hydration_reminder, source, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (plan_id, user_id, plan["breakfast"], plan["lunch"], plan["snack"],
             plan["dinner"], plan["nutrition_summary"], plan["hydration_reminder"],
             source, _now()),
        )
    return plan_id


def list_plans_for_user(user_id):
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM diet_plans WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def get_plan(plan_id, user_id):
    """User isolation: a plan is only returned if it belongs to user_id."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM diet_plans WHERE plan_id = ? AND user_id = ?",
            (plan_id, user_id),
        ).fetchone()
        return dict(row) if row else None


def delete_plan(plan_id, user_id):
    with get_connection() as conn:
        cur = conn.execute(
            "DELETE FROM diet_plans WHERE plan_id = ? AND user_id = ?",
            (plan_id, user_id),
        )
        return cur.rowcount > 0


# ---------------------------------------------------------------------------
# USER FILES  (metadata only — actual bytes live in cloud/storage_service.py)
# ---------------------------------------------------------------------------

def save_file_record(user_id, filename, storage_path, content_type):
    file_id = new_id()
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO user_files
               (file_id, user_id, filename, storage_path, content_type, uploaded_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (file_id, user_id, filename, storage_path, content_type, _now()),
        )
    return file_id


def list_files_for_user(user_id):
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM user_files WHERE user_id = ? ORDER BY uploaded_at DESC",
            (user_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def get_file(file_id, user_id):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM user_files WHERE file_id = ? AND user_id = ?",
            (file_id, user_id),
        ).fetchone()
        return dict(row) if row else None


def delete_file_record(file_id, user_id):
    with get_connection() as conn:
        cur = conn.execute(
            "DELETE FROM user_files WHERE file_id = ? AND user_id = ?",
            (file_id, user_id),
        )
        return cur.rowcount > 0
