# MetroFlow — AI Platform for Metro Crowd Management and Scheduling

Delivered through **Milestone 3 (Week 6)** — Milestones 1, 2, and 3 are complete.

## Scope by week

**Week 1 & 2 — User Management + Crowd Monitoring**
- JWT login, role-based access (admin / operator)
- Live station congestion, station analytics, congestion heatmap

**Week 3 & 4 — Scheduling + AI Prediction**
- Real per-station hourly capacity (replaces the old flat 6,000 placeholder)
- Real (simulated) train delay dataset, correlated with congestion patterns
- AI demand forecasting model (RandomForest) — predicts entries per station/hour
- AI delay forecasting model — predicts expected delay minutes per station/hour
- Train frequency recommendations, peak-hour summaries, delay-aware schedule adjustment

**Week 5 — Alerts & Notifications**
- Live overcrowding alerts (using real per-station capacity)
- Forecasted overcrowding alerts (using the AI demand model, before it happens)
- Delay notifications from the real delay dataset
- Emergency announcements (admin-only)
- Combined real-time alert feed for a dashboard ticker

**Week 6 — Analytics Dashboard (completes Milestone 3)**
- System-wide passenger traffic report (busiest/quietest stations)
- Station performance report (crowd + delay + AI insights combined)
- Live operational monitoring summary (system health, active delays)
- Congestion heatmap report with worst-congestion-point ranking
- Standalone AI insights report (forecast curve + recommendations)

Not yet built (Milestone 4, Week 7 & 8): application testing/validation, UI responsiveness work, Docker/cloud deployment, and final documentation/presentation.

## Datasets

| File | Schema | Purpose |
|---|---|---|
| `app/data/taipei_mrt_2yr.csv` | Date, Hour, Station, Entries, Exits | 2 years hourly ridership, 30 real Taipei stations |
| `app/data/station_capacity.csv` | Station, HourlyCapacity | Real per-station capacity, differentiated by station tier (interchange vs. outer) |
| `app/data/train_delays.csv` | Date, Hour, Station, DelayMinutes | Simulated delay events, correlated with congestion (busier hours → more/longer delays) |

All three follow real-world open-data schemas, so any of them can be swapped for genuine official data later with no code changes.

## Setup

```bash
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```
Open `http://127.0.0.1:8000/docs`.

**Demo logins:** `admin` / `admin123` (full access), `operator1` / `operator123` (station-scoped).

**First-time AI setup:** call `POST /ai/train` once (as admin) to train the demand and delay models — after that, predictions are instant. Endpoints will auto-train on first use if you skip this.

## Full endpoint list

**User Management**: `POST /auth/login`, `GET /auth/me`, `GET /admin/ping`

**Crowd Monitoring**: `GET /stations`, `GET /stations/capacity`, `GET /crowd/live`, `GET /crowd/station/{station}`, `GET /crowd/analytics/{station}`, `GET /crowd/heatmap`

**AI Prediction**: `POST /ai/train`, `GET /ai/predict/demand/{station}`, `GET /ai/predict/delay/{station}`, `GET /ai/forecast/{station}` (24hr forecast), `GET /ai/recommendations/{station}`

**Scheduling**: `GET /schedule/{station}`, `GET /schedule/{station}/peak-summary`, `GET /schedule/{station}/delay-report`, `GET /schedule/{station}/adjust-for-delay`

**Alerts**: `GET /alerts/overcrowding`, `GET /alerts/forecasted/{station}`, `GET /alerts/delays`, `POST /alerts/emergency`, `GET /alerts/live-feed`

**Analytics Dashboard**: `GET /analytics/traffic`, `GET /analytics/station/{station}`, `GET /analytics/operational-summary`, `GET /analytics/heatmap-report`, `GET /analytics/ai-insights/{station}`

**System**: `GET /`, `GET /health`

