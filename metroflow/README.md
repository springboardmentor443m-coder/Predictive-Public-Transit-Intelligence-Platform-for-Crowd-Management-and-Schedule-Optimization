# MetroFlow: AI Platform for Metro Crowd Management and Scheduling

A FastAPI service that monitors station crowding, forecasts passenger demand with a
machine-learning pipeline, recommends train frequency, raises alerts, and shows everything
on a web dashboard. Covers all four milestones of the 8-week brief.

| Milestone | Delivered |
|---|---|
| 1. Setup, auth, crowd monitoring | JWT login, admin/operator roles, live snapshot, station history, heatmap |
| 2. Scheduling and AI prediction | Demand forecast with 90% range, delay-risk model, train-frequency schedule, delay what-if |
| 3. Alerts and analytics | Overcrowding, forecast, delay and anomaly alerts, emergency broadcast, analytics reports, dashboard |
| 4. Testing, deployment, docs | 52 automated tests, Dockerfile and compose file, this README, ARCHITECTURE.md |

## Quick start

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows   (Mac/Linux: source .venv/bin/activate)
pip install -r requirements-dev.txt
python app/data/generate_dataset.py   # only if the CSVs in app/data are missing
python -m uvicorn app.main:app --port 8000
```

Open:
- http://127.0.0.1:8000/dashboard   visual dashboard
- http://127.0.0.1:8000/docs        Swagger UI (click Authorize after logging in)

Models train automatically on first use (about 20 seconds). `POST /ai/train` retrains them.

Demo accounts (in-memory, change before any real use):

| User | Password | Role |
|---|---|---|
| admin | admin123 | admin, all stations |
| operator1 | operator123 | operator, Taipei Main Station only |


## Dashboard features

The dashboard is served by FastAPI at `/dashboard` and uses the existing same-origin API and JWT session. It includes a responsive operations overview, dedicated live-simulation control room, station crowd index, crowd heatmap, forecast and recommended-frequency schedule, alerts center, station analytics, CSV exports, and an admin-only emergency-announcement form.

**Forecast horizon note:** the current ML pipeline predicts demand hourly. The dashboard displays +15- and +30-minute estimates by interpolating between adjacent hourly model predictions; these are not independently trained quarter-hour forecasts. The demo data is generated and “live” refers to the selected recorded hour, not a real-time transit feed. The emergency-announcement endpoint records a demo announcement and does not send actual SMS, push notifications, or public-address messages.

## Run tests

```bash
pytest -q
```

## Docker

```bash
docker compose up --build
```
The image trains the models during build. The app listens on port 8000.

## Data

Hourly entries and exits for 30 stations over two years (525,600 rows), plus station
capacity and train-delay events. The format follows the Taipei MRT open data schema, but
the values are **generated** by `app/data/generate_dataset.py` (seed 42) because the official
file could not be downloaded. Replace the CSVs in `app/data` with real data of the same
columns to use real numbers; `app/data/repository.py` is the only file that reads them.

## The machine-learning part

- Honest split: the last ~17% of time is held out and never used for training or model choice.
- Model selection by expanding-window cross-validation over 5 candidates, including a
  historical-average baseline that every model must beat.
- Chosen model: station/hour/weekday profile multiplied by a ridge-regression calendar factor
  (trend, yearly seasonality, holidays).
- 90% prediction intervals on a variance-stabilised scale, calibrated on the latest CV folds.
- Anomaly detector (z-score against the forecast) tested on injected spikes.
- Delay model: two stages (probability of delay, then severity) with gradient boosting.

Results on the untouched test period:

| Measure | Result |
|---|---|
| Mean absolute error | 24.5 vs 40.5 for the baseline (39.5% better) |
| 90% interval coverage | 91.4% |
| Spike detection | 100% of injected 50% surges; 0.97% false alarms |
| Delay model ROC-AUC | 0.61 (weak, see limitations) |

Full report: `GET /ai/model-report` or the dashboard panel.

## Main endpoints

Dates are `YYYY-MM-DD` inside the data range. Everything except `/`, `/health`, `/dashboard`
and `/auth/login` needs a Bearer token.

| Area | Endpoints |
|---|---|
| Auth | `POST /auth/login`, `GET /auth/me` |
| Crowd | `/stations`, `/stations/capacity`, `/crowd/live`, `/crowd/station/{s}`, `/crowd/analytics/{s}`, `/crowd/heatmap` |
| AI | `POST /ai/train`, `/ai/model-report`, `/ai/predict/demand/{s}`, `/ai/predict/delay/{s}`, `/ai/forecast/{s}`, `/ai/recommendations/{s}`, `/ai/anomalies` (admin), `/ai/anomaly-check/{s}` |
| Scheduling | `/schedule/{s}`, `/schedule/{s}/peak-summary`, `/schedule/{s}/delay-report`, `/schedule/{s}/adjust-for-delay` |
| Alerts | `/alerts/overcrowding`, `/alerts/forecasted/{s}`, `/alerts/delays`, `POST /alerts/emergency`, `/alerts/live-feed` (admin) |
| Analytics | `/analytics/traffic`, `/analytics/station/{s}`, `/analytics/ai-insights/{s}`, `/analytics/operational-summary` (admin), `/analytics/heatmap-report` (admin) |

Operators get 403 on any station other than their own.

## Known limitations

- The data is generated, so results show the method works, not how the real network behaves.
- The holiday windows in the model match the holidays invented in the generator.
- The delay model is weak (ROC-AUC 0.61): in this data delays are rare and only mildly linked to crowding.
- Users and the JWT secret are hard-coded for the demo. Use a database and an environment secret in production.
- "Live" means the latest hour in the dataset; there is no real-time feed.


## Simulated-live demo mode (no real transit feed required)

The dashboard includes an optional simulated-live stream for demonstrations. It samples the historical hourly profile for each station, applies a simple time-of-day demand factor and small per-tick variation, then recalculates capacity utilisation and demo alerts. It is explicitly labelled as simulated and is **not** real-time metro data.

1. Start the API: `python -m uvicorn app.main:app --reload --port 8000`.
2. Open `http://127.0.0.1:8000/dashboard` and sign in as the demo admin (`admin` / `admin123`).
3. On **Overview**, click **Start simulation**. Station values refresh approximately every five seconds while Overview is open.
4. Click **Stop simulation** to return to the selected historical snapshot.

Authenticated API endpoints:
- `GET /simulation/live` — current simulator state and snapshot.
- `POST /simulation/start` — start the simulator (admin only).
- `POST /simulation/stop` — stop the simulator (admin only).

The simulator is in-memory. Restarting the backend clears its state; it does not write simulated observations into the source CSV files. A real live deployment still requires an authorised transit data feed and must replace this demo source.


## Simulated-live operations mode

The Overview tab includes a simulated-live stream for demonstrations when no official metro feed is available. It generates station readings from historical hourly profiles, applies bounded variation, refreshes the in-memory snapshot every five seconds, and labels every reading as simulated. It is **not a real-time transit connection**.

Admins can select four demo scenarios:

- `normal`: historical profile with small random variation.
- `rush_hour`: higher simulated passenger demand.
- `demand_surge`: elevated demand with a stronger synthetic surge at one station.
- `service_disruption`: elevated demand plus generated delay alerts for a station.

The dashboard keeps a rolling history of the last 60 simulation ticks (in memory only). It resets when the server restarts. Operators only see their assigned station; network-wide history aggregates are hidden from operator accounts.

Authenticated endpoints:

- `GET /simulation/live` — current simulated snapshot, feed state, scenario and recent tick history.
- `POST /simulation/start` — start the simulated feed (admin only).
- `POST /simulation/stop` — stop the simulated feed (admin only).
- `POST /simulation/scenario` with `{"scenario":"rush_hour"}` — change scenario (admin only). Accepted values: `normal`, `rush_hour`, `demand_surge`, `service_disruption`.

These scenarios are for UI/testing demonstrations only. They do not dispatch trains, change real timetables, or represent verified operational measurements.


## Power Edition: persistent simulated-live operations

This edition adds a dedicated **Live simulator** control-room view while preserving the existing FastAPI app and historical dashboard.

### New capabilities
- Normal, rush-hour, demand-surge and service-disruption demo scenarios.
- Adjustable simulation refresh interval (3–60 seconds).
- Per-station entries, exits, net flow, capacity utilisation, status and simulated delay display.
- Persistent SQLite snapshots (up to 10,000) and a bounded operations event log (up to 2,000 events); history survives backend restarts.
- Admin-only endpoints for network-wide history, audit events and CSV export.
- More explicit health response (`real_time_connected: false`) and configurable JWT secret/CORS allowlist.

### New API endpoints
- `GET /simulation/history?limit=100` — persisted snapshots (admin only).
- `GET /simulation/events?limit=50` — control/audit events (admin only).
- `GET /simulation/export.csv?limit=500` — download snapshot history (admin only).
- `POST /simulation/start?interval_seconds=5` — start at a 3–60 second interval (admin only).

### Configuration
Copy `.env.example` to `.env` and set `METROFLOW_SECRET_KEY` to a long, unique random secret before deployment. Configure `METROFLOW_ALLOWED_ORIGINS` as a comma-separated allowlist for any separate frontend. The application does not automatically load `.env`; export the variables in your shell or configure them in your deployment environment. Do not use the demo accounts or default development secret in production.

### Important data distinction
The simulator derives synthetic readings from historical station profiles. It is **not a real-time transit connection**, does not control trains, and should not be used for actual service decisions. Persistent snapshots record demo runs only.

### Tests
Install `requirements-dev.txt`, then run `pytest -q`. The full test suite requires all runtime dependencies, including `bcrypt`, to be installed.
