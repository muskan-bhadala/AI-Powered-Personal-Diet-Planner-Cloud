# AI-Powered Personal Diet Planner with Cloud Storage

A cloud-computing course project: a full-stack app that generates
personalized example meal plans, stores them per-user in a cloud
database, and stores uploaded files in cloud object storage — runnable
entirely for free, locally, with a clean path to real cloud deployment.

> **Disclaimer:** All data is synthetic/demo data. Generated meal plans
> are general wellness / educational examples only — **not** medical or
> clinical nutrition advice. Consult a qualified professional for real
> dietary decisions.

## Overview

Users register, fill in a demo profile (age, height, weight, activity
level, dietary preference, goal), and generate a one-day meal plan
(breakfast/lunch/snack/dinner + a rough calorie summary + a hydration
reminder). Plans are saved to a database and can be revisited from any
device; users can also upload demo files (images/exports) to simulated
cloud object storage.

## Problem statement & objectives

People struggle to plan meals and stay consistent, and a purely local
app can't be accessed across devices or scaled to many users. This
project demonstrates, hands-on, how cloud computing concepts (managed
database, object storage, stateless auth, REST APIs, deployment,
scaling) solve that — using a diet planner as the vehicle, not as the
end goal in itself.

## Features

- Register / log in / log out (JWT-based, stateless auth)
- Demo profile: age, height, weight, activity level, dietary
  preference, goal, optional allergies
- Generate a plan: breakfast, lunch, snack, dinner, nutrition summary,
  hydration reminder — vegetarian, vegan, or non-vegetarian; general,
  weight-management-demo, or fitness-oriented-demo goals
- Save / list / view / delete generated plans
- Upload / list / download / delete demo files (cloud object storage)
- Dashboard aggregating profile, latest plan, and stats
- AI engine with **automatic fallback**: tries an external AI API only
  if explicitly enabled, otherwise (and on any failure) uses a local
  rule-based engine — the project never breaks due to a missing API key

## Cloud computing concepts demonstrated

See [`docs/cloud_concepts.md`](docs/cloud_concepts.md) for the full
table mapping every concept (SaaS/PaaS/IaaS, object storage vs
database, REST, serverless, scalability, elasticity, load balancing,
API gateway, env vars, secrets management, security, logging,
monitoring, deployment, CI/CD) to exactly where it appears in this repo.

## Architecture

See [`docs/architecture.md`](docs/architecture.md) for the full layered
diagram and data-flow explanation. Short version:

```
Browser → Frontend (static HTML/JS) → REST API (Flask)
                                          ├── AI engine (rule-based + fallback)
                                          ├── Cloud database service (SQLite locally)
                                          └── Cloud storage service (local folder)
```

Both cloud-facing services live behind a single file each
(`cloud/database_service.py`, `cloud/storage_service.py`), so swapping
in a real managed database or bucket later doesn't touch the rest of
the app.

## Technology stack (as built — "Option A/B hybrid")

- **Frontend:** plain HTML/CSS/JavaScript (no build step, easy to grade/run)
- **Backend:** Python + Flask, REST API
- **Auth:** JWT (PyJWT) + Werkzeug password hashing
- **Database:** SQLite (simulating a managed cloud database)
- **Storage:** local folder (simulating cloud object storage / S3 / Firebase Storage)
- **AI:** rule-based recommendation engine, with an optional external
  AI API call and automatic fallback

Three fuller stack options (beginner / recommended / advanced,
including a real AWS/Azure/GCP variant) are compared in
[`docs/deployment.md`](docs/deployment.md).

## AI recommendation engine

`ai_engine/diet_engine.py`:
- **Version A (default):** rule-based, using `ai_engine/food_data.json`,
  the user's dietary preference, activity level, and goal.
- **Version B (optional):** calls an external AI API if
  `USE_AI_API=true` and `AI_API_KEY` is set. On any failure (disabled,
  missing key, network error, bad response), it **automatically falls
  back** to Version A — see `generate_plan()`.

## Authentication

Register → password hashed (never stored plain) → login issues a
12-hour JWT → every protected route decodes and verifies that JWT and
scopes all reads/writes to that `user_id`. See
[`docs/security.md`](docs/security.md).

## Database design

`users`, `diet_plans`, `user_files` — see
[`docs/architecture.md`](docs/architecture.md) and
`cloud/database_service.py` for the full schema, keys, and
relationships.

## Cloud storage

`cloud/storage_service.py` stores uploaded file bytes under
`storage_bucket/<user_id>/...`; `user_files` in the database stores
only the metadata (filename, storage path, owner, timestamp) — the
same database/storage split used by real cloud apps.

## REST APIs

| Method | Path | Auth | Purpose |
|---|---|---|---|
| POST | `/api/register` | – | Create account |
| POST | `/api/login` | – | Get a JWT |
| POST | `/api/logout` | – | Stateless logout |
| GET | `/api/profile` | ✓ | Get profile |
| PUT | `/api/profile` | ✓ | Update profile |
| POST | `/api/generate-plan` | ✓ | Generate + save a plan |
| GET | `/api/plans` | ✓ | List your plans |
| GET | `/api/plans/<id>` | ✓ | Get one plan |
| DELETE | `/api/plans/<id>` | ✓ | Delete a plan |
| POST | `/api/upload` | ✓ | Upload a file |
| GET | `/api/files` | ✓ | List your files |
| GET | `/api/files/<id>` | ✓ | Download a file |
| DELETE | `/api/files/<id>` | ✓ | Delete a file |
| GET | `/api/health` | – | Health check |

## Folder structure

```
AI-Personal-Diet-Planner-Cloud/
├── frontend/                # Static HTML/CSS/JS UI
│   ├── index.html
│   ├── css/style.css
│   ├── js/api.js
│   └── pages/                (register, login, profile, generate,
│                               plan_result, saved_plans, files, dashboard)
├── backend/
│   ├── app.py                # Flask entrypoint, blueprint registration
│   ├── routes/                (auth, profile, plans, files)
│   └── utils/auth_utils.py   # Password hashing + JWT
├── ai_engine/
│   ├── diet_engine.py        # Rule-based + optional AI API + fallback
│   └── food_data.json
├── cloud/
│   ├── database_service.py   # "Cloud database" (SQLite locally)
│   └── storage_service.py    # "Cloud object storage" (local folder)
├── tests/test_app.py         # pytest suite, see docs/testing.md
├── sample_data/               # Synthetic demo users + seeding script
├── docs/                      # architecture, security, scalability,
│                               deployment, testing, GitHub strategy,
│                               screenshot checklist, local setup guide
├── screenshots/               # Put your captured screenshots here
├── requirements.txt
├── .env.example
└── .gitignore
```

## Installation & local setup

Full exact commands: [`docs/local_setup.md`](docs/local_setup.md).
Quick version:

```bash
cd AI-Personal-Diet-Planner-Cloud
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env      # then set a real JWT_SECRET inside
python backend/app.py
```
Open `http://localhost:5000`.

## Environment variables

See [`.env.example`](.env.example) — `JWT_SECRET`, `DATABASE_PATH`,
`STORAGE_BUCKET_PATH`, `USE_AI_API`, `AI_API_KEY`. Never commit a real
`.env` file (already covered by `.gitignore`).

## Cloud deployment

Two full approaches (free-tier PaaS, and AWS/Azure/GCP) in
[`docs/deployment.md`](docs/deployment.md), including a CI/CD example.

## Testing

```bash
pytest
```
Test plan and results table: [`docs/testing.md`](docs/testing.md).

## Security

[`docs/security.md`](docs/security.md) — auth vs authorization,
password hashing, user isolation, secrets management, HTTPS,
encryption, rate limiting, common mistakes to avoid.

## Scalability

[`docs/scalability.md`](docs/scalability.md) — how the architecture
would evolve at 10 / 1,000 / 100,000 users (autoscaling, load
balancing, serverless, managed DB replicas, CDN, queues).

## Screenshots

Capture and save into `screenshots/` following
[`docs/screenshots_checklist.md`](docs/screenshots_checklist.md), then
embed them here, e.g.:
```markdown
![Dashboard](screenshots/15_user_dashboard.png)
```

## Results

The app runs fully offline/locally with zero paid services, supports
the complete register → profile → generate → save → revisit → upload →
download flow, and passes all automated tests in `tests/test_app.py`
(20 test cases covering auth, plan generation for every preference/goal,
AI-fallback behavior, file handling, and cross-user data isolation).

## Limitations

- SQLite and local folder storage are single-machine simulations, not
  actually distributed/highly-available (by design, for a free
  student project) — see `docs/deployment.md` for the real-cloud swap.
- The rule-based AI engine picks from a fixed, synthetic food dataset;
  it is not a clinically validated nutrition tool.
- No password-reset-by-email flow (out of scope for this demo).

## Future improvements

- Swap in a real managed database/storage bucket (contained change,
  see `docs/architecture.md`).
- Add rate limiting on `/api/login` and `/api/register`.
- Add PDF export of a saved plan.
- Add a Coach review role for shared/reviewed plans.

## Learning outcomes

Hands-on practice with: REST API design, JWT-based stateless auth,
the database-vs-object-storage split, environment-variable-based
secrets management, automated testing, and planning a path from a
free local simulation to a real cloud deployment.

## Author

Built as a Cloud Computing course project. Replace this section with
your name, GitHub profile link, and course/institution details.
