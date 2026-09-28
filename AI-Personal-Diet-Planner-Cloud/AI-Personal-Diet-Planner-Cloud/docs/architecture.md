# System Architecture

## Layered view

```
CLIENT LAYER
  Web Browser
    │
    ▼
  Frontend (frontend/*.html, css/, js/) — plain HTML/CSS/JS, no build step

APPLICATION LAYER
  REST API (backend/app.py + backend/routes/*)
    │  Flask app, JWT-protected routes

AI LAYER
  ai_engine/diet_engine.py
    │  Rule-based recommendation engine (always available)
    │  Optional external AI API call with automatic fallback

DATA LAYER
  cloud/database_service.py
    │  Structured data: users, diet_plans, user_files (metadata)
    │  SQLite locally — swappable for a managed cloud DB (Firestore/RDS/Supabase)

STORAGE LAYER
  cloud/storage_service.py
    │  File bytes (images, exports)
    │  Local "storage_bucket/" folder — swappable for S3 / Firebase Storage / GCS

AUTHENTICATION
  backend/utils/auth_utils.py
       Password hashing (Werkzeug) + stateless JWT tokens
```

## Full request flow

```
User
  ↓
Web Application (frontend/*.html)
  ↓
Authentication (JWT attached as Authorization: Bearer <token>)
  ↓
User Profile Input (profile.html -> PUT /api/profile)
  ↓
Cloud Backend / REST API (backend/app.py, backend/routes/*)
  ↓
AI Diet Planner (ai_engine/diet_engine.py: AI API attempt -> fallback to rule-based)
  ↓
Personalized Plan (JSON: breakfast, lunch, snack, dinner, nutrition_summary)
  ↓
Cloud Database (cloud/database_service.py -> diet_plans table)
  ↓
Cloud Storage (cloud/storage_service.py -> user_files, for uploaded images/exports)
  ↓
User Dashboard (dashboard.html aggregates profile + plans + files)
```

## Why this design is "cloud swappable"

Every call to persistent state goes through exactly two files:
`cloud/database_service.py` (structured data) and
`cloud/storage_service.py` (files/blobs). Nothing in `backend/routes/*`
or the frontend talks to SQLite or the filesystem directly. This means
moving from the free local simulation to a real managed cloud database
or object storage bucket is a change contained to those two files —
the routes, the AI engine, and the entire frontend do not need to change.
This mirrors the "repository pattern" used in real production backends
specifically so a team can change infrastructure providers without
rewriting business logic.

## Data flow: Cloud Database vs Cloud Object Storage

- **Cloud Database** (`database_service.py`): structured rows with fixed
  columns you can query/filter/sort (a user's profile, a diet plan's
  meals, a file's metadata). Analogous to Firestore/DynamoDB/RDS.
- **Cloud Object Storage** (`storage_service.py`): opaque bytes (an
  image, a PDF export) addressed by a key/path, not by SQL columns.
  Analogous to S3 / Google Cloud Storage / Firebase Storage.

A `user_files` row in the database stores *metadata* (filename, who
owns it, when it was uploaded) while the *actual bytes* live in object
storage — this is exactly how real cloud apps separate the two
concerns, and both are demonstrated end-to-end in this project.
