# Scalability

## 10 users
The current architecture handles this easily on a single free-tier
instance: one Flask process, SQLite (or a single small managed DB
instance), and a local/small object storage bucket. No changes needed.

## 1,000 users
- SQLite becomes a bottleneck under concurrent writes → move to a
  managed cloud database (Postgres on RDS/Cloud SQL, or Firestore).
  Because all DB access already goes through `cloud/database_service.py`,
  this is a contained change.
- Run more than one backend instance behind a **load balancer** so
  traffic is spread across processes and a crashed instance doesn't
  take the whole app down.
- Move static frontend assets (the `frontend/` folder) onto a **CDN**
  so they're served from edge locations instead of the API server.
- Add basic **caching** (e.g. cache the food dataset in memory — already
  done — and consider caching read-heavy endpoints like `/api/plans`).

## 100,000 users
- **Autoscaling**: run the backend as a managed autoscaling group or as
  serverless functions (AWS Lambda / Cloud Run / Cloud Functions) that
  scale instance/container count with real-time demand instead of a
  fixed number of servers.
- **Managed database with read replicas**: separate read traffic
  (dashboard, plan history) from write traffic (registration, plan
  generation) across replicas.
- **API Gateway**: put a managed gateway in front of serverless
  functions for routing, auth checks, and throttling instead of hand-
  rolling that in Flask.
- **Queues**: if AI-plan generation becomes slow or rate-limited by an
  external AI API, push generation requests onto a queue (SQS/Pub-Sub)
  and process them asynchronously, notifying the user when ready,
  instead of holding an HTTP connection open.
- **Object storage at scale**: S3/GCS/Firebase Storage already scale
  to this level natively — no extra work needed there, which is exactly
  why cloud object storage is used instead of a local disk in production.
- **CDN** in front of both static assets and, if useful, cached API
  responses for anonymous/public data.

## Talking points for interviews

- Stateless auth (JWT) is what makes horizontal scaling straightforward
  here — any backend instance can validate any request without shared
  session state.
- The repository-pattern split between `database_service.py` and
  `storage_service.py` is what lets the same codebase scale from
  "SQLite on a laptop" to "managed Postgres + S3" without touching
  business logic in `backend/routes/`.
- Elasticity (scale up AND back down) matters as much as scaling up —
  serverless/autoscaling groups also save cost during low-traffic
  periods, which a fixed-size server fleet cannot do.
