# Milestone 4 — Weeks 7 & 8: Analytics, Testing & Final Deployment

> PRD scope: Develop analytics dashboard for historical trends and performance reports ·
> Conduct end-to-end testing of AI predictions and alert accuracy · Optimize system
> performance and scalability · Deploy platform using Docker and cloud environments ·
> Prepare final documentation and project presentation.

## 1. Analytics Dashboard

- `GET /analytics/overview` — fleet KPIs: total stations/trains, active schedules,
  avg platform occupancy, on-time %, open alerts.
- `GET /analytics/traffic?hours=N&start_time=ISO` — hourly entries/exits series
  (Recharts area chart); `start_time` replays a chosen historical day.
- `GET /analytics/station-performance?limit=N&hours=N&start_time=ISO` — per-station
  report card: ridership, punctuality %, peak congestion; scoped to a rolling or
  as-of historical window.
- UI: `pages/dashboard/analytics.jsx` (KPI cards, radar + bar reports, historical
  data tracker, performance table) and Settings → admin user management.

## 2. End-to-End Testing

Automated suite: `backend/tests/test_api.py` (54 API tests) + `test_model_wrappers.py` (10 model tests) = **64 tests** in those two files (179 across the full suite), all passing, run with:

```bash
cd backend && pip install -r requirements-dev.txt
pytest tests/test_api.py -v
```

Coverage by module:

| Area | Verified behaviors |
|---|---|
| Auth/RBAC | login success/failure, token guard, role 403s, admin user list, self-registration locked to viewer role, `PUT /users/me` profile & password updates |
| Crowd | live snapshots, heatmap grid size, station history, history with custom `start_time` anchor |
| Predictions | crowd forecast shape, demand ≥ 0, recommendations, traffic patterns, `start_time` date-aware windows (multi-day weekday handling), per-train route forecast |
| Trains | live fleet telemetry, single-train lookup + 404, train schedule stops, fleet registry sync |
| Scheduling | viewer blocked, CRUD round-trip, delay→alert linkage, apply-headway |
| Alerts | broadcast admin-only, acknowledge flow |
| Analytics | overview counts, station performance bounds, windowed station performance + traffic with `start_time`, AI insights panel |
| System | crowd ingest RBAC, alert type/severity/station filters, single-schedule fetch, model-info provenance, delay 503 fallback |

Manual E2E: seeded demo data (10 stations, 12 trains, ~1700 schedules over 8 days,
plus 7 days of ridership history), three demo roles; frontend production build
passes (`npm run build`).

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
| Analytics dashboard delivering actionable insights | ✅ insights + model badge (AI Predictions page) + CSV/print |
| System tested end-to-end with reliable AI outputs | ✅ 53 automated API tests + 10 model tests |
| Platform deployed and accessible via Docker/cloud setup | ✅ compose + k8s + cloud docs |
| Complete documentation and presentation delivered | ✅ |

## Outcomes (PRD)

Strengthened deployment and DevOps skills; learned to translate analytical outputs into
operational dashboards; delivered a complete, tested, documented smart transportation
platform.

## Addendum -- Post-Milestone-4 Engineering Hardening

Delivered on branch `KOKKIRIGADDA-MANOJ-BABU` after M4 wrap-up:

- **Frontend fully TypeScript** -- every page/component/lib converted .js/.jsx -> .ts/.tsx;
   tsc --noEmit and npm run build green.
- **Public health endpoint** -- GET /api/v1/health (login page + k8s probes); login no longer
  probes an auth-protected route (fixes false *Backend Offline*).
- **Chart resilience** -- analytics/crowd-history charts gained loading + empty states; dark-theme
  chart tooltips use explicit item/label colours so the values stay readable on every chart.
- **Crowd history for any past date** -- `GET /crowd/station/{id}/history` synthesises a full
  daily occupancy curve (weekend-aware, mirrored from the simulation clock's row model so entries
  and exits stay distinct) when the chosen window predates the stored history; the UI also anchors
  a date chosen while *Start Hour* is "Now" at midnight instead of emitting an invalid query.
- **Realistic traffic curve** -- schedules now respect headways (4-min peak / 8-min off-peak),
  so the Network Traffic Trend shows real rush-hour shape instead of a flat line; each line's
  within-hour departure grid is staggered per train code so the timetable no longer collapses
  every train onto the same :00/:08/… minutes.
- **Advanced ML** -- quantile GradientBoosting crowd model with native lower/upper intervals
  (docs/ML_MODELS.md).
- **Dataset importers** -- MTA / Seoul / TfL real CSV ingestion feeding the seed pipeline
  (docs/IMPORTERS.md).
- **Python hygiene** -- `datetime.utcnow()` fully replaced by `app.core.time.utcnow()`;
  modern | None type hints.
- **Real NYC subway (59 stations)** -- stations.csv swapped ST01–ST10 demo codes for 59 genuine
  MTA stop ids across eight trunk corridors (1/2/3, 4/5/6, 7, A/C/E, B/D/F/M, L, N/Q/R/W and the
  Staten Island Railway); crowd/demand models retrained on them
  (`nyc_train_metrics.json`: crowd R² 0.981, demand R² 0.969) and made the default
  (`METROFLOW_MODEL_CITY=nyc`); capacity ceiling aligned to a real station
  (`MAX_CAPACITY=14600`) and rolling stock modelled on real MTA car classes (R160/R143/R179/R211).
- **GTFS connection graph** -- scripts/build_connections.py derives the real junction graph
  (25 edges: 21 along-line + 4 walking interchanges) from the official MTA feed via the
  parent_station normalisation (platform `120N` → station `120`), served at
  `GET /api/v1/crowd/connections` (tested: 8 tests).
- **Full-network geographic map** -- scripts/build_network.py snapshots the entire real network
  (496 stations / 578 rail segments) into data/nyc_network.json, served at
  `GET /api/v1/crowd/network` (tested: 8 tests). The Crowd dashboard's *geographic* toggle now
  draws the complete rail network as a faint base layer with the 59 monitored stations and their
  live congestion overlaid, while the original schematic view is untouched. A third *connections*
  toggle isolates a single junction: everything the selected station is not directly linked to
  drops to 14%, each of its own links lights up with a route chip, and a side panel lists the same
  links. Highlighting uses the tested `linkTouches` predicate so only links genuinely incident to
  the selection light up. Map fidelity note: stations, coordinates and adjacency are real MTA
  GTFS data, but the line between two stops is drawn straight (no `shapes.txt` polylines) -- see
  PROJECT_GUIDE.md 4.1.
- **Testing** -- backend suite grown from 59 to **179 tests** (54 API, 27 simulation, 21 timezone,
  19 ML artifacts, 14 cache/live, 10 features, 10 model wrappers, 8 connections, 8 network,
  8 scheduling advice); frontend Vitest suite **45 tests**.
