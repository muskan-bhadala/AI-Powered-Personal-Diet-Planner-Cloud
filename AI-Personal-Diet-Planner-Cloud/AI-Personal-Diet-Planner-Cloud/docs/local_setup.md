# Local / Virtual Simulation — Exact Commands

Run every step from inside the `AI-Personal-Diet-Planner-Cloud/` folder
unless noted otherwise.

## Step 1 — Install required software
Install Python 3.10+ and Git if you don't already have them.
Check versions:
```bash
python3 --version
git --version
```

## Step 2 — Clone/create the project
If you downloaded this as a zip, just unzip it and `cd` in:
```bash
cd AI-Personal-Diet-Planner-Cloud
```
Or, once it's on GitHub:
```bash
git clone https://github.com/<your-username>/AI-Powered-Personal-Diet-Planner-Cloud.git
cd AI-Powered-Personal-Diet-Planner-Cloud
```

## Step 3 — Create a Python virtual environment
```bash
python3 -m venv .venv
source .venv/bin/activate        # on Windows: .venv\Scripts\activate
```

## Step 4 — Install dependencies
```bash
pip install -r requirements.txt
```

## Step 5 — Configure environment variables
```bash
cp .env.example .env
```
Open `.env` and set `JWT_SECRET` to a random value:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```
Paste the output as `JWT_SECRET=...` in `.env`.

## Step 6 — Start the backend (also serves the frontend)
```bash
python backend/app.py
```
You should see Flask start on `http://0.0.0.0:5000`.

## Step 7 — Open the frontend
There is no separate frontend server — Flask serves it. Open:
```
http://localhost:5000
```

## Step 8 — Register a demo user
In the browser: click **Get started**, fill in a name/email/password
(8+ characters), and submit.

*(Optional, instead of using the browser)*: run the seeding script to
create several demo users at once (needs the backend running and
`requests` installed):
```bash
python sample_data/seed_demo_data.py
```

## Step 9 — Complete the profile
On the **Profile** page, fill in age, height, weight, activity level,
dietary preference, goal, and (optionally) allergies, then **Save profile**.

## Step 10 — Generate a diet plan
Go to **Generate new plan** → **Generate plan**. You'll be redirected
to the result page showing breakfast/lunch/snack/dinner and a nutrition
summary.

## Step 11 — Save the plan
Plans are saved automatically when generated — check **View saved plans**
to confirm it's listed.

## Step 12 — Upload a sample file
Go to **Files**, choose a small `.png`/`.jpg`/`.pdf`/`.txt`/`.csv` file
(under 5 MB), and click **Upload**.

## Step 13 — Retrieve a previous plan
On **Saved plans**, confirm your earlier plan is still listed with its
timestamp.

## Step 14 — Test logout/login
Click **Log out**, then log back in with the same email/password on the
**Log in** page — your profile and plans should still be there.

## Step 15 — Verify stored data
Structured data: open `cloud_db.sqlite3` (created automatically in the
project root after step 6) with any SQLite browser, or run:
```bash
python -c "
from cloud import database_service as db
db.init_db()
print(db.get_user_by_email('<the email you registered>'))
"
```
File data: check the `storage_bucket/<your_user_id>/` folder — your
uploaded file should be there under a randomized filename.

## Running the automated tests
```bash
pytest
```
All test cases from `docs/testing.md` should pass.
