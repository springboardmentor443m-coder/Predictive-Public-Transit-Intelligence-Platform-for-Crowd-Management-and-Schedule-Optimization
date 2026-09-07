# MetroFlow — Cloud Deployment Guide

The platform ships with `docker-compose.yml` for single-host deployment and
`deploy/k8s/metroflow.yaml` for Kubernetes. This guide covers AWS and Azure,
per PRD Milestone 4 ("Deploy platform using Docker and cloud environments").

## 0. Prerequisites

- Docker images built and pushed to a registry:
  ```bash
  docker build -t <registry>/metroflow-backend:1.0 ./backend
  docker build -t <registry>/metroflow-frontend:1.0 ./frontend
  docker push <registry>/metroflow-backend:1.0
  docker push <registry>/metroflow-frontend:1.0
  ```
- Before building the frontend image, pass the public API URL:
  ```bash
  docker build --build-arg NEXT_PUBLIC_API_URL=https://api.your-domain.com -t <registry>/metroflow-frontend:1.0 ./frontend
  ```
  `NEXT_PUBLIC_API_URL` is baked into the browser bundle at **build time**.
  - If the API is reachable from browsers at its own domain, set it to that URL
    (and allow that origin in the backend `CORS_ORIGINS`).
  - For Kubernetes/same-origin deployments (no public API hostname), build with
    `--build-arg NEXT_PUBLIC_API_URL=` (empty). The app then calls same-origin
    `/api/v1/*` and `/socket.io/*`, and the Next server proxies them to
    `BACKEND_INTERNAL_URL` at runtime — see §3.

## 1. AWS Deployment

Reference architecture (all managed):

| Component | AWS Service |
|---|---|
| Backend API (FastAPI + Socket.IO) | ECS Fargate (or App Runner) |
| Frontend (Next.js) | ECS Fargate / App Runner / S3+CloudFront (static export) |
| PostgreSQL | RDS PostgreSQL 16 |
| MongoDB | DocumentDB (mongo-compatible) |
| Redis | ElastiCache for Redis |
| Secrets | AWS Secrets Manager |
| Container registry | Amazon ECR |

Steps:

1. **RDS**: create PostgreSQL 16 instance (`metroflow`), note endpoint.
2. **DocumentDB**: create cluster; connection string replaces `MONGODB_URL`.
3. **ElastiCache**: create Redis cluster; endpoint replaces `REDIS_URL`.
4. **Secrets Manager**: store `DATABASE_URL`, `MONGODB_URL`, `REDIS_URL`, `JWT_SECRET_KEY`.
5. **ECS Task Definition** (backend): container port 8000, env from secrets.
   Health check: `GET /api/v1/health`. Note: Socket.IO needs sticky sessions —
   use an ALB with `stickiness.enabled = true` on the target group.
6. **ALB**: HTTP 80/443 → backend target group (:8000) and frontend (:3000),
   path-based routing `/api/*` and `/socket.io/*` → backend.
7. **Scale**: backend service autoscaling on CPU 60%, min 2 tasks.

One-command alternative: AWS App Runner for both images (no ALB config needed;
enable session affinity for the backend service).

## 2. Azure Deployment

| Component | Azure Service |
|---|---|
| Backend + Frontend | Azure Container Apps |
| PostgreSQL | Azure Database for PostgreSQL Flexible Server |
| MongoDB | Azure Cosmos DB for MongoDB (vCore or RU) |
| Redis | Azure Cache for Redis |
| Registry | Azure Container Registry (ACR) |

Steps:

1. `az group create -n metroflow-rg -l eastus`
2. Create PostgreSQL Flexible Server, Cosmos DB (Mongo), Azure Cache for Redis.
3. `az acr build --registry <acr> --image metroflow-backend:1.0 ./backend` (same for frontend).
4. `az containerapp env create` then two `az containerapp create` calls:
   - backend: ingress port 8000, external, session affinity enabled
     (`--session-affinity cookie`), secrets via `--secrets` + `--env-vars`.
   - frontend: ingress port 3000, external, `NEXT_PUBLIC_API_URL=https://<backend-fqdn>`.
5. Health probes: `GET /api/v1/health`.

## 3. Kubernetes (any cloud)

```bash
kubectl apply -f deploy/k8s/metroflow.yaml
kubectl -n metroflow get svc frontend   # external IP
```

Frontend networking: the manifest sets `NEXT_PUBLIC_API_URL=""` and
`BACKEND_INTERNAL_URL=http://backend.metroflow.svc.cluster.local:8000`. Browsers
talk to the frontend origin only; the Next server proxies `/api/v1/*` and
`/socket.io/*` to the in-cluster backend (cluster DNS is not reachable from
browsers, so the API URL must never point at `localhost` or an internal service
name). **Build the frontend image with `--build-arg NEXT_PUBLIC_API_URL=`**
(empty) when targeting this manifest — the variable is compiled into the client
bundle at build time.

For production: replace in-cluster postgres/mongo/redis with managed services,
set strong `JWT_SECRET_KEY` in `metroflow-secrets`, and add an Ingress with TLS
(cert-manager) instead of the LoadBalancer service.

## 4. Post-deploy checklist

- [ ] `GET https://<host>/api/v1/health` returns `{"status": "ok"}`
- [ ] Login works against the deployed API (CORS origin set to the dashboard URL)
- [ ] Socket.IO connects (Overview page shows "Socket connected")
- [ ] Run seed once against the production DB:
      `python scripts/seed_db.py` (with prod `DATABASE_URL`)
- [ ] Train models are present in the image or mounted volume (`models_store/*.joblib`);
      otherwise run `python scripts/train_models.py` as a one-off job
