MetroFlow — Milestone 1 (Week 1 & 2)
Project Initialization, Design Process & Core Setup
This delivers exactly the Week 1 & 2 scope from your plan:
[x] Define project objectives and transportation workflows
[x] Design system architecture and database schema (see `ARCHITECTURE.md`)
[x] Setup backend environment (FastAPI)
[x] Implement authentication and role-based access system
[x] Build crowd monitoring dashboard (API)
[x] Develop congestion tracking features
Scheduling, AI demand forecasting, alerts, and the full analytics dashboard
are Week 3+ — not included here on purpose. Ask for "Week 3 & 4" when
you're ready and I'll build the Scheduling + AI Prediction modules on top
of this same foundation.
---
1. Data source
`app/data/taipei_mrt_2yr.csv` — 2 years (Jan 2022–Dec 2023), hourly,
30 real Taipei Metro stations, columns: `Date, Hour, Station, Entries, Exits`.
This matches the schema of the official dataset
(data.gov.tw #128683) exactly, so
you can drop in the real download later by overwriting this CSV — no code
changes needed anywhere else in the app.
Regenerate it any time with:
```bash
python3 app/data/generate_dataset.py
```
2. Setup
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
Open http://127.0.0.1:8000/docs for interactive Swagger docs.
3. Demo credentials (User Management Module)
Username	Password	Role
admin	admin123	admin
operator1	operator123	operator
Login: `POST /auth/login` (form-encoded `username`/`password`) → returns a JWT.
Pass it as `Authorization: Bearer <token>` on every other endpoint.
4. Endpoints delivered this milestone
User Management
`POST /auth/login` — get JWT
`GET /auth/me` — current user profile
`GET /admin/ping` — admin-only route (RBAC demo)
Crowd Monitoring
`GET /stations` — list all 30 stations
`GET /crowd/live?on_date=&hour=` — live density + congestion status, system-wide
`GET /crowd/station/{station}?on_date=&hour=` — single station snapshot
`GET /crowd/analytics/{station}?days=30` — station-wise analytics (avg entries/exits, peak hour, inflow/outflow balance)
`GET /crowd/heatmap?on_date=` — station × hour congestion matrix (for the dashboard heatmap)
`GET /health` — service + dataset status check.
5. Verified
Ran an end-to-end smoke test: login → list stations → live congestion → station
analytics → heatmap → admin route. All 200 OK. Sample: at hour 8 on the latest
date in the dataset, system-wide entries ≈29k across 30 stations, Taipei Main
Station's peak hour comes out to 18:00 (evening rush), matching the real-world
pattern the dataset was built from.
