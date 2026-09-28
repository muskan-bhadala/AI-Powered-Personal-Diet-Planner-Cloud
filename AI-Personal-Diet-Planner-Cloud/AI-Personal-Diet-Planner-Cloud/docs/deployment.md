# Cloud Deployment

## Local Development vs Cloud Deployment

| | Local development | Cloud deployment |
|---|---|---|
| Backend | `python backend/app.py` on your laptop | Managed platform runs the same code |
| Database | SQLite file on disk | Managed cloud database (Postgres/Firestore) |
| Storage | `storage_bucket/` folder | S3 / Firebase Storage / GCS bucket |
| Secrets | `.env` file (never committed) | Platform's environment-variable panel / secret manager |
| Access | `http://localhost:5000` only | Public HTTPS URL, reachable from any device |

---

## Approach A — Student-friendly / free-tier deployment

This keeps the project's free-tier-first design intact.

1. Push the repository to GitHub (see `docs/github_strategy.md`).
2. Create a free account on a PaaS such as Render, Railway, or
   PythonAnywhere.
3. Create a new "Web Service" pointing at your GitHub repo.
4. Set the start command: `python backend/app.py`
   (or `gunicorn backend.app:app` if the platform expects a WSGI server —
   add `gunicorn` to `requirements.txt` if so).
5. Add environment variables in the platform's dashboard, copying the
   keys from `.env.example` (`JWT_SECRET`, `PORT`, etc.). Generate a
   real random `JWT_SECRET` — do not reuse the example value.
6. Deploy. The platform builds from `requirements.txt` and starts the
   app; you get a public HTTPS URL.
7. **Database/storage note**: most free-tier PaaS filesystems are
   *ephemeral* (wiped on redeploy). For a persistent cloud database,
   create a free Postgres instance (e.g. on the same platform, or
   Supabase) and update `cloud/database_service.py` to use it instead
   of SQLite; for persistent storage, create a free Firebase Storage or
   S3-compatible bucket and update `cloud/storage_service.py`
   accordingly. Both files are intentionally isolated so this is a
   small, contained change (see `docs/architecture.md`).
8. Check platform logs/monitoring dashboard after deploy; hit
   `GET /api/health` to confirm the service is live.

## Approach B — AWS / Azure / GCP architecture

A production-style version of the same architecture:

- **Frontend hosting**: static `frontend/` files on S3 + CloudFront
  (AWS), Azure Static Web Apps, or Cloud Storage + Cloud CDN (GCP).
- **Backend hosting**: containerize `backend/` (Dockerfile running
  `gunicorn backend.app:app`) and deploy to AWS ECS/Fargate or App
  Runner, Azure App Service, or Google Cloud Run. For a fully
  serverless variant, individual routes (e.g. `/api/generate-plan`)
  could become AWS Lambda functions behind API Gateway.
- **Managed database**: Amazon RDS (Postgres), Azure Database for
  PostgreSQL, or Cloud SQL — replacing the SQLite calls inside
  `cloud/database_service.py`.
- **Object storage**: Amazon S3, Azure Blob Storage, or Google Cloud
  Storage — replacing the local folder in `cloud/storage_service.py`.
- **Authentication**: keep the existing JWT approach, or swap in a
  managed identity provider (Amazon Cognito, Azure AD B2C, Firebase
  Auth) if you want managed password resets/social login.
- **Environment variables**: AWS Systems Manager Parameter
  Store/Secrets Manager, Azure Key Vault, or GCP Secret Manager.
- **Logs & monitoring**: CloudWatch, Azure Monitor, or Cloud Logging +
  Cloud Monitoring, watching the `GET /api/health` endpoint for uptime.

## CI/CD

A minimal CI/CD pipeline (e.g. GitHub Actions) for this project:

```yaml
# .github/workflows/ci.yml (example — create this file if you want CI)
name: CI
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -r requirements.txt
      - run: pytest
```

Run `pytest` automatically on every push; only deploy (Approach A or B)
if the tests pass. Most PaaS platforms (Render/Railway) auto-deploy on
push to `main` once connected to the GitHub repo, which completes the
CI/CD loop without extra configuration.
