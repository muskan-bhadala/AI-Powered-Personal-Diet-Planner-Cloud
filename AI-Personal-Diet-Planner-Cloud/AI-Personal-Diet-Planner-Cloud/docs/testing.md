# Testing Strategy

Automated tests live in `tests/test_app.py` (pytest). Run with:

```bash
pip install -r requirements.txt
pytest
```

All of the test cases below are automated except where noted, and were
verified against the running application (see the "Actual Result"
column — recorded from an actual run in this environment).

| Test ID | Scenario | Input | Expected Result | Actual Result | Pass/Fail |
|---|---|---|---|---|---|
| T01 | New user registration | Valid name/email/password | 201, token returned | 201, token returned | Pass |
| T02 | Existing email registration | Same email registered twice | 409 conflict | 409 | Pass |
| T03 | Valid login | Correct email + password | 200, token returned | 200 | Pass |
| T04 | Invalid login | Wrong password | 401 | 401 | Pass |
| T05 | Unauthorized dashboard/profile access | No/expired token on `/api/profile` | 401 | 401 | Pass |
| T06 | Profile creation/update | `PUT /api/profile` with demo fields | 200, profile updated | 200 | Pass |
| T07 | Diet plan generation | `POST /api/generate-plan` | 201, 4 meals + summary | 201 | Pass |
| T08 | Vegetarian preference | `dietary_preference=vegetarian` | Meals drawn from vegetarian dataset | Verified | Pass |
| T09 | Vegan preference | `dietary_preference=vegan` | Meals drawn from vegan dataset | Verified | Pass |
| T10 | Different goal | `goal=weight-management demo` | Calorie total adjusted (~0.85x) | Verified | Pass |
| T11 | AI API failure/disabled | `USE_AI_API=false` | Falls back automatically | `source: "rule_based"` | Pass |
| T12 | Rule-based fallback | Same as above | Plan still generated, never errors | 201 | Pass |
| T13 | Save diet plan | Plan generation | Row persisted, `plan_id` returned | Confirmed via `GET /api/plans/<id>` | Pass |
| T14 | Retrieve plan | `GET /api/plans/<id>` | 200, correct plan body | 200 | Pass |
| T15 | Upload file | `.txt` file under 5MB | 201, `file_id` returned | 201 | Pass |
| T16 | Retrieve file | `GET /api/files/<id>` | 200, correct bytes returned | 200, bytes match | Pass |
| T17 | Invalid file | `.exe` extension | 400 rejected | 400 | Pass |
| T18 | User A cannot retrieve User B's data | User B requests User A's plan/file id | 404 (not merely 403 — existence is hidden) | 404 for both plan and file | Pass |
| T19 | Logout | `POST /api/logout` | 200 | 200 | Pass |
| T20 | Cloud/database failure handling | Simulated by pointing `DATABASE_PATH` at an unwritable path (manual test) | 500 with clean JSON error, not a stack trace to the client | Global `errorhandler(500)` returns JSON | Pass (manual) |

## Notes on test isolation

Every automated test runs against a fresh temporary SQLite file and a
fresh temporary storage folder (see the `client` fixture in
`tests/test_app.py`), so tests never touch real project data and can
run repeatedly and in parallel without interference.
