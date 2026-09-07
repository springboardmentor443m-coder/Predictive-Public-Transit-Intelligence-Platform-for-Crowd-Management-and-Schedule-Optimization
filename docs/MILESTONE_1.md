# Milestone 1 — Weeks 1 & 2: Project Initialization, Design Process & Core Setup

> PRD scope: Define objectives and transportation workflows · Design system architecture
> and database schema · Create UI wireframes and operational workflow planning · Setup
> frontend and backend environments · Implement authentication and role-based access
> system · Build crowd monitoring dashboard · Develop congestion tracking features.

## 1. Objectives Defined

- Platform goal: monitor passenger flow, predict crowd density, and optimize train
  scheduling in real time for metro operations.
- Workflows modeled: gate entry/exit → station occupancy → congestion classification →
  alerting; timetable management → delay handling → frequency adjustment.
- Explicit constraint honored: **no computer vision / CCTV** — all intelligence derives
  from ticketing, footfall, ridership, GPS/status and operational datasets.

## 2. System Architecture

Documented in [`PROJECT_PLAN.md`](PROJECT_PLAN.md) §2:

```
Next.js Dashboard ──REST + Socket.IO──▶ FastAPI Services ──▶ PostgreSQL (core)
                                                        ├──▶ MongoDB   (raw events)
                                                        └──▶ Redis     (live cache)
FastAPI Services ──▶ scikit-learn models (joblib artifacts)
```

## 3. Database Schema

| Store | Collections/Tables | Purpose |
|---|---|---|
| PostgreSQL | `users`, `stations`, `trains`, `train_schedules`, `ridership_records`, `alerts` | Relational core (SQLAlchemy models in `backend/app/models/`) |
| MongoDB | `metroflow.sensor_events` | Raw smart-card swipes + density snapshots (`app/core/mongo.py`) |
| Redis | `crowd:latest:{station_id}` | 30s live-snapshot cache with in-memory fallback (`app/core/cache.py`) |

## 4. UI Wireframes / Workflow Planning

Dashboard information architecture (implemented in `frontend/pages/dashboard/`):

1. **Overview** — KPI strip, live station density board, alerts feed, traffic chart.
2. **Crowd Monitoring** — station cards, station×hour heatmap, inflow/outflow drill-down.
3. **Scheduling** — optimizer strip, timetable table with CRUD, delay actions.
4. **AI Predictions** — forecast charts with confidence bands, patterns, recommendations.
5. **Alerts** — filterable feed, acknowledge flow, emergency broadcast console.
6. **Analytics** — KPIs, radar/bar reports, station performance report card table.

## 5. Environments Setup

- Backend: Python venv, FastAPI + SQLAlchemy + Pydantic v2 (`backend/requirements.txt`).
- Frontend: Next.js 14 + Tailwind CSS + Recharts + socket.io-client (`frontend/package.json`).
- Config via `.env` (see `backend/.env.example`, `frontend/.env.example`).

## 6. Authentication & RBAC — Implementation

| Item | Where | Notes |
|---|---|---|
| JWT issuance | `app/api/v1/auth.py` | OAuth2 password flow, HS256, role claim |
| Password hashing | `app/core/security.py` | pbkdf2_sha256 via passlib |
| Token validation | `app/core/deps.py` | `get_current_user` dependency |
| Role enforcement | `app/core/deps.py` | `require_roles(*roles)` — admin/operator/viewer |
| Admin user CRUD | `app/api/v1/users.py` | list/create/update/deactivate (admin only) |
| Profile management | Settings page + `PUT /users/{id}` | name/password self-service |

Verified by tests: `tests/test_api.py::test_login_rejects_bad_password`,
`test_viewer_cannot_list_users`, `test_me_requires_token`.

## 7. Crowd Monitoring Dashboard & Congestion Tracking

- Live snapshots per station: occupancy %, congestion level (low/medium/high/critical),
  inflow/outflow rates — `app/services/crowd_service.py`.
- Congestion thresholds: ≥55% medium, ≥75% high, ≥90% critical.
- Heatmap generation across stations × 24h — `GET /api/v1/crowd/heatmap`.
- Station history (inflow/outflow) — `GET /api/v1/crowd/station/{id}/history`.
- Frontend: `pages/dashboard/index.jsx`, `pages/dashboard/crowd.jsx`,
  `components/HeatmapGrid.jsx`.

## Evaluation Criteria Checkpoint (PRD §6, Week 2)

| Criterion | Status |
|---|---|
| Project initialization and architecture setup completed | ✅ |
| Authentication and operator management implemented | ✅ |
| Crowd monitoring dashboard functional | ✅ |
| System design and UI planning completed | ✅ |

## Outcomes (PRD)

Understood smart transportation workflows; learned architecture + DB design; initialized
frontend/backend projects; delivered working authentication and crowd monitoring system.
