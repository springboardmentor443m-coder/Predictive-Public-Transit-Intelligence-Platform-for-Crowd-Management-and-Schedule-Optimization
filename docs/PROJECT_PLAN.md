# MetroFlow — Project Implementation Plan

Derived strictly from the PRD: *MetroFlow: AI Platform for Metro Crowd Management and Scheduling*.

## 1. Objectives

- Monitor passenger flow and station congestion in real time (ticketing + sensor datasets, no CCTV/CV).
- Predict crowd density and passenger demand with ML models.
- Optimize train scheduling and frequency, especially during peak hours.
- Deliver operational alerts, emergency notifications, and analytics dashboards.
- Deploy a scalable Python backend + modern web frontend via Docker/cloud.

## 2. System Architecture

```
┌───────────────────────────── Browser (Next.js Dashboard) ─────────────────────────────┐
│  Login │ Overview │ Crowd Monitoring │ Scheduling │ AI Predictions │ Alerts │ Analytics │
└──────────────┬──────────────────────────────── REST (JSON) ────────┬──────────────────┘
               │                                        Socket.IO live channel
               ▼                                                        ▼
┌──────────────────────────────── FastAPI Backend (Python) ────────────────────────────┐
│  api/v1: auth │ users │ stations │ crowd │ scheduling │ predictions │ alerts │ analytics│
│  services: crowd_service │ scheduling_service │ prediction_service │ alert_service     │
│            analytics_service │ realtime (Socket.IO broadcaster)                        │
│  ml/: feature engineering → scikit-learn crowd model + demand forecaster (joblib)      │
└───────┬───────────────────────┬──────────────────────────┬────────────────────────────┘
        ▼                       ▼                          ▼
   PostgreSQL              MongoDB                    Redis
 (users, stations,      (raw ticketing &          (live crowd snapshot
  trains, schedules,     sensor events,             cache, pub/sub for
  ridership agg,          entry/exit logs)           real-time fanout)
  alerts)
```

## 3. Data Model (PostgreSQL core)

| Table | Purpose | Key fields |
|---|---|---|
| users | auth + RBAC | email, hashed_password, full_name, role(admin/operator/viewer), is_active |
| stations | network topology | code, name, line, zone, capacity_per_hour, lat/lng |
| trains | fleet | code, model, capacity, status(active/maintenance) |
| train_schedules | timetable | train_id, station_id, direction, arrival, departure, headway_min, status(on_time/delayed/cancelled), delay_min |
| ridership_records | hourly aggregated footfall per station | station_id, timestamp, entries, exits, occupancy, congestion_level |
| alerts | alert engine output | type(overcrowding/delay/emergency/info), severity, station_id, message, is_acknowledged |

MongoDB `metroflow.sensor_events`: raw smart-card swipes / gate counts / APC sensor payloads.
Redis keys: `crowd:latest:{station_id}` snapshots, `alerts:recent` list.

## 4. Week-wise Plan (PRD milestones)

### Milestone 1 — Weeks 1–2: Initialization, Design & Core Setup
- [x] Define objectives + transportation workflows (`docs/PROJECT_PLAN.md`)
- [x] System architecture + PostgreSQL/MongoDB/Redis schema design
- [x] UI wireframes & operational workflow planning (dashboard suite below)
- [x] Frontend (Next.js+Tailwind) & backend (FastAPI) environment setup
- [x] Authentication: JWT login, refresh-safe storage, role-based access control
- [x] Crowd monitoring dashboard: KPIs, live occupancy, heatmap, inflow/outflow
- [x] Congestion tracking features (thresholds, levels, station drill-down)

### Milestone 2 — Weeks 3–4: Scheduling System & AI Prediction
- [x] Train scheduling workflows (CRUD, status transitions, delay handling)
- [x] Frequency adjustment system + peak-hour optimizer (demand→headway solver)
- [x] Real-time operational monitoring (Socket.IO live feed)
- [x] Crowd prediction models trained on passenger datasets (scikit-learn)
- [x] Passenger demand forecasting algorithms (hourly/daily horizon)
- [x] Traffic analysis reports (peak detection, pattern analysis)

### Milestone 3 — Weeks 5–6: Alerts, Notifications & Analytics
- [x] Notification & alert workflows (rule engine on live occupancy/delays)
- [x] Emergency announcement system (broadcast to all dashboard clients)
- [x] Real-time schedule update features (socket push + polling fallback)
- [x] Analytics & reporting dashboards (traffic, station performance, punctuality)
- [x] Congestion heatmaps + operational insights panels

### Milestone 4 — Weeks 7–8: Testing, Deployment & Documentation
- [x] API smoke tests + workflow validation scripts
- [x] Responsive UI polish and optimization
- [x] Docker Compose deployment (frontend, backend, postgres, mongo, redis)
- [x] Final documentation (README, plan, API docs at /docs)

## 5. API Surface (v1)

| Method | Path | Role | Description |
|---|---|---|---|
| POST | /api/v1/auth/login | public | JWT login |
| GET | /api/v1/auth/me | any | current profile |
| PUT | /api/v1/users/me | any | update profile/password |
| GET/POST | /api/v1/users | admin | manage operators |
| GET | /api/v1/stations | any | network stations |
| GET | /api/v1/crowd/live | any | live density per station |
| GET | /api/v1/crowd/heatmap | any | heatmap matrix (station × hour) |
| GET | /api/v1/crowd/station/{id}/history | any | inflow/outflow history |
| GET/POST/PUT/DELETE | /api/v1/scheduling/schedules | operator+ | schedule management |
| GET | /api/v1/scheduling/optimization | operator+ | frequency recommendations |
| POST | /api/v1/scheduling/delay/{schedule_id} | operator+ | report/handle delay |
| GET | /api/v1/predictions/crowd?station_id&hours | any | crowd forecast |
| GET | /api/v1/predictions/demand?station_id&hours | any | demand forecast |
| GET | /api/v1/predictions/recommendations | any | smart recommendations |
| GET | /api/v1/alerts | any | alerts feed |
| POST | /api/v1/alerts/{id}/acknowledge | operator+ | acknowledge |
| POST | /api/v1/alerts/broadcast | admin | emergency announcement |
| GET | /api/v1/analytics/overview | any | KPI summary |
| GET | /api/v1/analytics/traffic | any | traffic analytics series |
| GET | /api/v1/analytics/station-performance | any | station report cards |
| WS | /socket.io | any | live crowd + alert events |

## 6. Performance Targets (PRD §8–9)

- Density estimation & congestion prediction accuracy tracked at training time (R²/MAE reported by trainer).
- Live update latency < 2 s via Socket.IO broadcast loop.
- Recommended headways reduce modeled platform over-capacity minutes during peaks.
- API p95 response < 300 ms on seeded dataset; concurrent monitoring supported via async broadcast.

## 7. Risk & Mitigation

| Risk | Mitigation |
|---|---|
| No real transit feed available | Deterministic synthetic dataset generator mimicking smart-card patterns (peaks, weekends, holidays) |
| Model drift | Retrain script + joblib versioned artifacts; metrics logged each run |
| DB unavailability in dev | Redis/Mongo optional with graceful in-memory fallback; SQLite fallback documented for offline demos |
