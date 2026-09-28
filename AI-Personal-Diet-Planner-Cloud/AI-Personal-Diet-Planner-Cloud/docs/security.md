# Cloud Security Notes

## What this project already does

- **Password security**: passwords are never stored in plain text.
  `backend/utils/auth_utils.py` uses Werkzeug's salted hash
  (`generate_password_hash` / `check_password_hash`).
- **Authentication vs authorization**: *authentication* proves who you
  are (login issues a JWT); *authorization* decides what you're allowed
  to touch (every plan/file route re-checks `user_id` from the token
  against the row's owner before returning data — see "user isolation"
  below).
- **Authentication tokens / JWT**: `create_token`/`decode_token` in
  `auth_utils.py`. Tokens are signed with `JWT_SECRET`, expire after 12
  hours, and are stateless (no server-side session store needed, which
  helps scalability — see `docs/scalability.md`).
- **User isolation**: every database read in `cloud/database_service.py`
  that returns a plan or file filters by `WHERE user_id = ?` in addition
  to the record's own id, so User A can never fetch User B's data even
  by guessing an id. Covered by `tests/test_app.py::test_user_isolation_on_plans_and_files`.
- **Environment variables & secrets management**: `JWT_SECRET`,
  `AI_API_KEY`, and storage/database paths are read from environment
  variables (see `.env.example`), never hardcoded. `.env` is excluded
  via `.gitignore`.
- **Input validation**: email format, password length, allowed
  `activity_level`/`dietary_preference` values, allowed file extensions,
  and a 5 MB file size cap are all validated server-side, not just in
  the browser.
- **CORS**: a minimal `Access-Control-Allow-*` header set in
  `backend/app.py` explicitly controls which origins/methods can call
  the API, rather than leaving it unset.

## What a real cloud deployment adds

- **HTTPS / encryption in transit**: terminate TLS at the cloud
  provider's load balancer or platform (Render/Railway/AWS ALB/etc.);
  Flask itself does not need to handle certificates.
- **Encryption at rest**: managed cloud databases and object storage
  (RDS, Firestore, S3, Firebase Storage) encrypt data on disk by
  default — enable this explicitly if a provider makes it optional.
- **Secrets management**: in production, use the provider's secret
  manager (AWS Secrets Manager, GCP Secret Manager, or the PaaS's
  dashboard "Environment Variables" panel) instead of a `.env` file on
  disk.
- **Database access rules / IAM**: a managed database should have a
  narrowly-scoped service account/role, not a shared admin credential.
- **Object storage permissions**: buckets should default to *private*;
  only signed, time-limited URLs (or an authenticated API route, as
  this project does) should ever serve a file.
- **Rate limiting**: add a reverse-proxy or API gateway rate limit
  (e.g. Cloudflare, AWS API Gateway throttling) in front of `/api/login`
  and `/api/register` to slow brute-force attempts.
- **Logging & monitoring**: ship logs to a managed log service
  (CloudWatch, Cloud Logging) and set up alerts on error rate/latency.
- **Backups**: enable automated snapshots on the managed database and
  versioning on the storage bucket.

## Common mistakes students should avoid

- Committing a real `.env` file or API key to GitHub (double-check
  `git status` before every commit).
- Storing passwords in plain text or with a fast, unsalted hash.
- Trusting `user_id` sent in a request body instead of the one decoded
  from the verified JWT (always take identity from the token, never
  from client-supplied fields).
- Leaving a cloud storage bucket public "just to make it work" during
  development and forgetting to lock it back down.
- Printing secrets to logs for debugging and forgetting to remove it.
