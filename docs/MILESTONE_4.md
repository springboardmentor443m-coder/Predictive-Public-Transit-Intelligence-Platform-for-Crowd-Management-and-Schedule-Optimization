# Milestone 4 — Weeks 7 & 8: Analytics, Testing & Final Deployment

> PRD scope: Develop analytics dashboard for historical trends and performance reports ·
> Conduct end-to-end testing of AI predictions and alert accuracy · Optimize system
> performance and scalability · Deploy platform using Docker and cloud environments ·
> Prepare final documentation and project presentation.

## 1. Analytics Dashboard

- `GET /analytics/overview` — fleet KPIs: total stations/trains, active schedules,
  avg platform occupancy, on-time %, open alerts.
- `GET /analytics/traffic?hours=N` — hourly entries/exits series (Recharts area chart).
- `GET /analytics/station-performance?limit=N` — per-station report card: ridership,
  punctuality %, peak congestion, delay minutes.
- UI: `pages/dashboard/analytics.jsx` (KPI cards, radar + bar reports, performance
  table) and Settings → admin user management.

## 2. End-to-End Testing

Automated suite: `backend/tests/test_api.py` (32 tests, all passing) run with:

```bash
cd backend && pip install -r requirements-dev.txt
pytest tests/test_api.py -v
```

Coverage by module:

| Area | Verified behaviors |
|---|---|
| Auth/RBAC | login success/failure, token guard, role 403s, admin user list, self-registration locked to viewer role, `PUT /users/me` profile & password updates |
| Crowd | live snapshots, heatmap grid size, station history |
| Predictions | crowd forecast shape, demand ≥ 0, recommendations, traffic patterns |
| Scheduling | viewer blocked, CRUD round-trip, delay→alert linkage, apply-headway |
| Alerts | broadcast admin-only, acknowledge flow |
| Analytics | overview counts, station performance bounds, traffic series |

Manual E2E: seeded demo data (10 stations, 12 trains, ~170 schedules, 60 days of
ridership), three demo roles; frontend production build passes (`npm run build`).

## 3. Performance & Scalability

Measured results in [`PERFORMANCE_METRICS.md`](PERFORMANCE_METRICS.md). Key levers:

- Redis caching of live snapshots (30s TTL) with in-memory fallback.
- MongoDB retry cooldown (60s) so missing services never block the event loop.
- Socket.IO broadcast loop runs DB work via `asyncio.to_thread`.
- Stateless backend → horizontal scale (2 replicas in k8s manifests, ALB sticky
  sessions for socket affinity).

## 4. Deployment

- **Docker**: `backend/Dockerfile`, `frontend/Dockerfile`, root `docker-compose.yml`
  (postgres, mongo, redis, backend, frontend).
- **Kubernetes**: `deploy/k8s/metroflow.yaml` — namespace, secrets, PVC-backed
  postgres, mongo, redis, backend (readiness/liveness probes on `/api/v1/health`),
  frontend LoadBalancer.
- **Cloud guides**: [`DEPLOYMENT.md`](DEPLOYMENT.md) — AWS (ECS Fargate + RDS +
  DocumentDB + ElastiCache + ALB) and Azure (Container Apps + Flexible Server +
  Cosmos DB + Azure Cache).

## 5. Documentation & Presentation

- `README.md` — quickstart, architecture, module map, API surface.
- `docs/PROJECT_PLAN.md` — master plan; `MILESTONE_1..4.md` — this series.
- `docs/PERFORMANCE_METRICS.md` — model + API benchmarks.
- `postman/MetroFlow.postman_collection.json` — full API collection with auto-token
  login request for demos/reviewers.

## Evaluation Criteria Checkpoint (PRD §6, Week 8)

| Criterion | Status |
|---|---|
| Analytics dashboard delivering actionable insights | ✅ |
| System tested end-to-end with reliable AI outputs | ✅ 32 automated tests |
| Platform deployed and accessible via Docker/cloud setup | ✅ compose + k8s + cloud docs |
| Complete documentation and presentation delivered | ✅ |

## Outcomes (PRD)

Strengthened deployment and DevOps skills; learned to translate analytical outputs into
operational dashboards; delivered a complete, tested, documented smart transportation
platform.
