# Cloud Computing Concepts Demonstrated

| Concept | Where it appears in this project |
|---|---|
| Cloud Computing (general) | The whole app is designed around on-demand, remotely-accessible compute + storage rather than a purely offline script. |
| SaaS | The finished, deployed app itself — a user just visits a URL and uses it; no install. |
| PaaS | Deploying `backend/` to a platform such as Render/Railway/PythonAnywhere/Heroku-style hosting: you supply code, the platform manages the OS/runtime. |
| IaaS (where applicable) | Deploying the same backend to a raw AWS EC2 / Azure VM / GCP Compute Engine instance instead (see `docs/deployment.md` Approach B) — you manage the OS. |
| Cloud Storage (object storage) | `cloud/storage_service.py` — file uploads, simulated locally, mapped 1:1 to S3/Firebase Storage/GCS calls in code comments. |
| Cloud Database | `cloud/database_service.py` — `users`, `diet_plans`, `user_files` tables/collections. |
| Object Storage vs Database | See the comparison in `docs/architecture.md`. |
| Authentication | `backend/routes/auth_routes.py` + `backend/utils/auth_utils.py` — register/login/logout, password hashing, JWTs. |
| REST API | `backend/routes/*.py` — resource-oriented endpoints (`/api/plans`, `/api/files`) using standard HTTP verbs and status codes. |
| Client-Server Architecture | `frontend/` (client) talks only over HTTP to `backend/` (server); never touches the database or storage directly. |
| Serverless Computing | Discussed in `docs/deployment.md` Approach B — how `/api/generate-plan` could become an AWS Lambda / Cloud Function instead of a long-running Flask process. |
| Scalability | `docs/scalability.md` — 10 vs 1,000 vs 100,000 users. |
| Availability | Health check endpoint `GET /api/health`, used by uptime monitors/load balancers to detect and route around unhealthy instances. |
| Elasticity | `docs/scalability.md` — autoscaling groups / serverless concurrency scaling up and back down with demand. |
| Load Balancing | `docs/scalability.md` — distributing requests across multiple backend instances once traffic grows past one server. |
| API Gateway | `docs/scalability.md` / `docs/deployment.md` Approach B — a managed entry point (rate limiting, auth checks, routing) in front of serverless functions. |
| Environment Variables | `.env.example`, `python-dotenv` usage in `backend/app.py`, `cloud/database_service.py`, `cloud/storage_service.py`, `ai_engine/diet_engine.py` — no secret is ever hardcoded. |
| Secrets Management | `JWT_SECRET`, `AI_API_KEY` read only from environment variables; `.gitignore` excludes `.env`; `docs/security.md` explains cloud secret managers for production. |
| Cloud Security | `docs/security.md` — HTTPS, encryption at rest/in transit, password hashing, input validation, CORS, rate limiting. |
| Logging | `app.logger.exception(...)` in the global error handler in `backend/app.py`. |
| Monitoring | `GET /api/health` + notes in `docs/deployment.md` on connecting a cloud provider's monitoring dashboard. |
| Deployment | `docs/deployment.md` — two full approaches (free-tier PaaS, and AWS/Azure/GCP). |
| CI/CD | `docs/deployment.md` "CI/CD" section — running `pytest` automatically on every push before deploying. |
