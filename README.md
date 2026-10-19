# AI MetroFlow: Predictive Public Transit Intelligence Platform

**Crowd management and schedule optimization for Namma Metro (BMRCL, Bengaluru)**

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688)
![React](https://img.shields.io/badge/Frontend-React%20%2B%20Vite-61DAFB)
![XGBoost](https://img.shields.io/badge/ML-XGBoost-orange)

AI MetroFlow is an operational decision-support platform for the BMRCL metro network. It combines historical hourly station ridership, daily ridership and GTFS timetable data to monitor station demand, forecast ridership with XGBoost models, and suggest peak-hour headway adjustments to planners.

Built as part of the **Infosys Springboard Internship** by **Mahak Thavrani**.

[Overview](#-project-overview) • [Architecture](#-system-architecture) • [Data](#-data) • [AI & ML](#-ai--machine-learning) • [How Scores Are Calculated](#-how-scores-are-calculated) • [UI Pages](#-ui-pages) • [Directory Structure](#-directory-structure) • [Quick Start](#-quick-start) • [API Reference](#-api-reference) • [Limitations](#-data-transparency--limitations)

---

## 🌟 Project Overview

Metro planners need to know **which stations come under demand pressure, when, and how service should respond**. AI MetroFlow provides:

1. **Station monitoring**: hourly entries, exits and net flow per station, with an analytical *pressure score* and level (Low / Moderate / High / Critical).
2. **Demand forecasting**: a next-hour station ridership model, a future hourly station forecast (up to 90 days ahead), and a daily network ridership forecast.
3. **Scheduling intelligence**: station-level priority scores and recommended peak headways, GTFS route/trip/timetable browsing, and a workflow for saving frequency proposals and delay records.
4. **Analytics**: ridership trends, station comparison, passenger flow, station-hour heatmaps, statistical outlier screening and model insights.

All endpoints except the root and `/auth/*` routes require a JWT login.

---

## 🏛️ System Architecture

```
┌──────────────────────────────────────┐
│  React + Vite frontend (frontend/)   │  Dashboard · Network Monitoring · Crowd Monitoring
│  Axios client: src/services/api.js   │  Scheduling · AI Predictions · Live Monitoring & Analytics
└───────────────────┬──────────────────┘
                    │ REST + JWT  (http://127.0.0.1:8000)
┌───────────────────▼──────────────────┐
│  FastAPI backend (backend/app/)      │  routers → services → data / models
│  SQLite (ai_metroflow.db)            │  users, frequency proposals, delay records
└───────────────────┬──────────────────┘
                    │
┌───────────────────▼──────────────────┐
│  Data & ML layer                     │  data/bmrcl/  (ridership CSVs, GTFS files)
│  data/ · outputs/ · notebooks/       │  outputs/     (trained XGBoost models, scheduling analysis)
└──────────────────────────────────────┘
```

**Request flow:** a page calls `api.js` → a FastAPI router validates the request and the JWT → a service loads the CSV/GTFS data and runs the saved model → JSON returns to the page.

---

## 📊 Data

All data files live under `data/bmrcl/` and `outputs/`.

| File | Used for |
|---|---|
| `data/bmrcl/station-hourly.csv` | Hourly station **entries** (semicolon-separated: Date, Hour, Station, Ridership) |
| `data/bmrcl/station-hourly-exits.csv` | Hourly station **exits** (same format) |
| `data/bmrcl/daily-ridership.csv` | Daily network ridership by payment type (smart cards, tokens, NCMC, group tickets, QR) |
| `data/bmrcl/routes.txt`, `trips.txt`, `stop_times.txt`, `stops.txt`, `calendar.txt`, `calendar_dates.txt`, `frequencies.txt` | GTFS schedule data |
| `data/bmrcl/demo_2026/` | Optional demo copy of the hourly data with shifted dates (see below) |
| `outputs/station_scheduling_analysis.csv` | Precomputed station scheduling analysis used by the scheduling intelligence service |
| `outputs/*.joblib` | Trained models and encoders (see [AI & ML](#-ai--machine-learning)) |

**Data window:** hourly records are replayed from **12 Aug 2025 to 30 Sep 2025** (11 Aug is kept only to compute lag features). Earlier records are treated as incomplete and excluded from station totals. The test suite expects **83 stations**.

**Demo mode:** setting the environment variable `AI_METROFLOW_DEMO_2026=1` makes the prediction service read `data/bmrcl/demo_2026/` instead. Those dates are **shifted from historical data**; they are not real 2026 observations, and responses are labelled `simulated_2026_demo`. The demo data is produced by `backend/create_2026_demo_data.py`.

---

## 🧠 AI & Machine Learning

### 1. Station crowd model: next-hour ridership (XGBoost)

- **Files:** `outputs/xgboost_crowd_prediction_model_hourly_corrected.joblib`, `outputs/station_encoder.joblib`
- **Notebook:** `notebooks/BMRCL_Crowd_Prediction_ML.ipynb`
- **Target:** next-hour station entries
- **Features:** hour, day of week, day of month, month, weekend flag, peak-hour flag, current entries, current exits, net flow, previous-hour entries, previous-day entries, rolling 3-hour average, previous-hour exits, previous-hour net flow, plus the one-hot-encoded station.
- **Future hourly forecast:** for a target date/hour after the latest observation, the model is rolled forward **one hour at a time** (up to 90 days). Future exits are approximated with historical hourly medians, so errors accumulate over long horizons.

### 2. Daily demand model: network ridership (XGBoost)

- **Files:** `outputs/xgboost_demand_forecasting_model_v2.joblib`, `outputs/demand_forecasting_feature_names_v2.joblib`
- **Notebook:** `notebooks/BMRCL_Demand_Forecasting_ML.ipynb`
- **Features:** day of week, day of month, month, week of year, weekend flag, previous-day ridership, previous-week ridership, 7-day rolling average, demand change, 3-day rolling change.
- **Forecasts:** next day, 7 or 30 days ahead, or any specific future date. Multi-day forecasts are recursive.

### 3. Statistical outlier screening (not a trained model)

`/analytics/anomalies` flags station-hour totals outside **1.5 × IQR** of that station's own distribution. This is statistical screening, not a trained anomaly-detection model.

### 4. Ridership analysis

`notebooks/BMRCL_Ridership_Analysis.ipynb` contains exploratory analysis of station and time-of-day patterns.

### Model performance

These values are stored in `backend/app/services/analytics_service.py` and shown on the Analytics page.

| Model | MAE | RMSE | R² | Baseline MAE | Baseline RMSE | Baseline R² |
|---|---|---|---|---|---|---|
| Station crowd (next hour) | 45.53 | 84.36 | 0.9691 | 121.23 | 227.82 | 0.7745 |
| Daily demand | 75,797.70 | 109,753.18 | 0.5361 | 125,736.52 | 175,132.80 | −0.1812 |

- **Crowd model:** results come from the notebook's held-out test evaluation. The API does not recompute them. They describe **single next-hour predictions**, not the recursive multi-step forecasts.
- **Daily demand model:** trained on 276 rows and tested on 69 rows (test period 2026-05-01 to 2026-09-08). Its MAE is about 39.7% lower than the baseline, but R² is moderate, so treat long-horizon forecasts cautiously.
- Feature-importance values are shown for both models and describe model behavior, not causation.

---

## 🧮 How Scores Are Calculated

### Station pressure score (0–100)
Calculated in `monitoring_service.py` for each station and hour from:

| Component | Weight |
|---|---|
| Current entries scaled against the network-wide historical min–max | 0.40 |
| Predicted next-hour entries scaled the same way | 0.25 |
| Percentile rank of current entries among all stations at that hour | 0.20 |
| Percentile rank of predicted entries | 0.10 |
| Percentile rank of positive net flow | 0.05 |

If no prediction is available, the remaining components are re-weighted instead of inventing a value.

**Levels:** Low < 30 · Moderate 30–59 · High 60–84 · Critical ≥ 85.
The score is an analytical indicator, **not measured occupancy** or confirmed congestion.

### Historical demand status (Crowd Monitoring)
Per station, hour-of-day totals are compared with that station's other hours: **Low** ≤ 25th percentile, **High** > 75th percentile, otherwise **Moderate**. Peak periods: Morning 07–10, Midday 11–16, Evening 17–20, Off-peak otherwise.

### Alert rules (`alert_service.py`)
- Pressure score ≥ 60 → **High** alert; ≥ 80 → **Critical** alert
- Prediction vs observed next-hour ridership differs by ≥ 20% → **Moderate** "prediction deviation" alert

### Scheduling priority and recommended headway (`scheduling_intelligence_service.py`)
- Priority from the precomputed `Scheduling_Priority_Score`: **High** ≥ 0.50, **Moderate** ≥ 0.35, otherwise **Low**
- Recommended peak headway: High = 10% reduction plus up to 10% more by score; Moderate = 5% plus up to 5%; Low = unchanged. Results are limited to **4–20 minutes**.
- This is a planning heuristic. The frequency "what-if" endpoints only compare services per hour arithmetically and do not predict crowd reduction or waiting times.

---

## 🖥️ UI Pages

The sidebar contains these pages (all except Login require login):

| Route | Page | What it does |
|---|---|---|
| `/login` | **Login** | Sign in with a registered username and password; stores the JWT in the browser |
| `/` | **Dashboard** (Executive Operations Overview) | KPIs (stations monitored, high/critical pressure stations, alert signals, next-day demand forecast); a schematic map of up to 12 stations; station telemetry and a pressure-based assessment; recommended peak headway; pressure distribution. Uses the historical snapshot for 2025-09-30 18:00 |
| `/monitoring` | **Network Monitoring** | Refreshes `/monitoring/live` every 15 s (latest historical observations); daily ridership forecast for a chosen date; station cards with search, filter, sort and pagination; a station details drawer; high/critical pressure alert list |
| `/crowd-monitoring` | **Crowd Monitoring** | Simulated live network (refreshed every 5 s); network AI operations summary; station explorer with next-hour prediction and a future hourly forecast; station × hour demand heatmap; peak-demand, hotspot and passenger-flow tables; CSV export |
| `/scheduling` | **Scheduling** | Select the Green, Purple or Yellow line to browse GTFS stations, trips and frequencies; ML-based frequency analysis for a station, date and hour; save, approve, reject and complete frequency proposals; record delays (Manual or Demo source) |
| `/predictions` | **AI Predictions** | Next-day network demand forecast with data-freshness status; next-hour prediction for a station; scheduling recommendations table with a priority filter |
| `/analytics` | **Live Monitoring and Analytics** | Historical replay snapshots every 15 s; network overview; station pressure distribution; ridership trends; station comparison; highest-entry stations; passenger flow; statistical outliers; station-hour heatmap; model metrics; analytics-driven follow-up suggestions |

`/station-intelligence`, `/train-operations` and `/data-models` redirect to Crowd Monitoring, Network Monitoring and Analytics.

---

## 📁 Directory Structure

```
Predictive-Public-Transit-Intelligence-Platform-for-Crowd-Management-and-Schedule-Optimization/
├── backend/
│   ├── app/
│   │   ├── main.py                       # FastAPI app, CORS, router registration
│   │   ├── database.py                   # SQLite engine and session
│   │   ├── auth_utils.py                 # JWT validation (get_current_user)
│   │   ├── models/                       # user.py, scheduling.py (SQLAlchemy)
│   │   ├── schemas/                      # user.py, scheduling.py (Pydantic)
│   │   ├── routers/                      # alerts, analytics, auth, crowd, health,
│   │   │                                 # monitoring, operations, prediction, scheduling
│   │   └── services/
│   │       ├── alert_service.py
│   │       ├── analytics_service.py
│   │       ├── crowd_service.py
│   │       ├── demand_forecasting_service.py
│   │       ├── historical_replay_service.py
│   │       ├── live_simulation_service.py
│   │       ├── monitoring_service.py
│   │       ├── operations_service.py
│   │       ├── prediction_service.py
│   │       ├── scheduling_intelligence_service.py
│   │       └── scheduling_service.py
│   ├── tests/                            # unittest-based tests (5 files)
│   └── create_2026_demo_data.py          # Demo data generator
├── frontend/
│   └── src/
│       ├── App.jsx                       # Routes and protected layout
│       ├── components/AppLayout.jsx      # Sidebar and logout
│       ├── pages/                        # Dashboard, DemandPulse (Network Monitoring),
│       │                                 # CrowdMonitoring, Schedules, AIPredictions,
│       │                                 # Analytics, Login
│       │                                 # StationIntelligence and TrainOperations are
│       │                                 # present but not routed
│       ├── services/api.js               # Axios client and API functions
│       └── styles/                       # Page stylesheets
├── data/bmrcl/                           # Ridership CSVs, GTFS files, demo_2026/
├── outputs/                              # Trained models and scheduling analysis
├── notebooks/                            # Crowd, demand and ridership notebooks
├── metroflow-openapi.json                # OpenAPI specification
└── README.md
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10 or newer
- Node.js 18 or newer
- Git

### 1. Clone
```bash
git clone https://github.com/springboardmentor443m-coder/Predictive-Public-Transit-Intelligence-Platform-for-Crowd-Management-and-Schedule-Optimization.git
cd Predictive-Public-Transit-Intelligence-Platform-for-Crowd-Management-and-Schedule-Optimization
git checkout mahak-thavrani
```

### 2. Backend
Run everything from inside the `backend` folder, because the data paths and the SQLite file are relative to it.

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows  (Linux/macOS: source venv/bin/activate)

# Use backend/requirements.txt if present; otherwise install what the code imports:
pip install fastapi "uvicorn[standard]" sqlalchemy "python-jose[cryptography]" "passlib[bcrypt]" pandas numpy joblib xgboost scikit-learn

python -m uvicorn app.main:app --reload --port 8000
```
- Swagger docs: http://127.0.0.1:8000/docs
- If registering a user fails with a bcrypt error, install `bcrypt==4.0.1`.

**Create a user.** The frontend only has a login form, so register once through Swagger (`POST /auth/register`) with:
```json
{ "username": "demo", "email": "demo@example.com", "password": "your-password" }
```

**Optional demo mode** (PowerShell): `$env:AI_METROFLOW_DEMO_2026="1"` before starting the server.

### 3. Frontend
```bash
cd frontend
npm install
npm run dev
```
Open http://localhost:5173 and sign in. The frontend calls the API at `http://127.0.0.1:8000` (set in `src/services/api.js`), and the backend allows CORS from ports 5173 and 5174.

### 4. Tests
```bash
cd backend
python -m pytest tests/ -v
# or: python -m unittest discover -s tests -t .
```
Several tests use the real dataset (for example 2025-09-30 at 18:00), so the data files and trained models must be present.

---

## 📡 API Reference

Interactive documentation is available at `/docs`, and the full specification is in `metroflow-openapi.json`. Unless noted, endpoints require `Authorization: Bearer <token>`.

| Group | Endpoints |
|---|---|
| **General** | `GET /` (public) · `GET /health` |
| **Auth** (public) | `GET /auth/status` · `POST /auth/register` · `POST /auth/login` |
| **Crowd** (`/crowd`) | `/stations` · `/hourly` · `/daily` · `/peak-periods` · `/hotspots` · `/status` · `/flow` · `/heatmap` · `/demand-pressure` |
| **Monitoring** (`/monitoring`) | `/summary?date&hour` · `/live` · `/stations/{station}?date&hour` · `/demo-live` (simulated) · `/replay/next` (historical replay) |
| **Alerts** (`/alerts`) | `/summary?date&hour` · `/stations/{station}?date&hour` |
| **Operations** (`/operations`) | `/summary?date&hour` · `/stations/{station}?date&hour` |
| **Prediction** (`/prediction`) | `POST /crowd` · `GET /crowd/latest/{station}` · `GET /crowd/forecast/{station}/{target_date}/{target_hour}` · `GET /demand` · `GET /demand/forecast/{days}` (7 or 30) · `GET /demand/date/{target_date}` |
| **Scheduling, GTFS** (`/scheduling`) | `/routes` · `/routes/{route_id}/stations` · `/routes/{route_id}/trips` · `/routes/{route_id}/frequency` · `/trips/{trip_id}/schedule` · `/trips/{trip_id}/frequency` · `/trips/{trip_id}/service` · `/trips/{trip_id}/service-dates` · `/trips/{trip_id}/active-status?service_date` · `/service-dates?trip_id` · `/active-status?trip_id&service_date` |
| **Scheduling, intelligence** | `GET /scheduling/intelligence/summary` · `GET /scheduling/intelligence/stations/{station}` · `GET /scheduling/frequency/what-if` · `GET /scheduling/frequency/analysis` |
| **Scheduling, records** | `POST` and `GET /scheduling/proposals` · `PATCH /scheduling/proposals/{id}` · `POST` and `GET /scheduling/delays` |
| **Analytics** (`/analytics`) | `/overview` · `/trends` · `/anomalies?limit` · `/stations?limit` · `/passenger-flow` · `/hotspots?limit` · `/model-insights` · `/heatmap` |

---

## 🔍 Data Transparency & Limitations

- **No live data feeds.** The system does not connect to live turnstile, train GPS or delay feeds. `/monitoring/live` returns the latest observations in the historical dataset (`is_live_feed: false`), `/monitoring/replay/next` replays history at 1× clock speed, and `/monitoring/demo-live` is a **simulation** built from a historical baseline with small random changes. The Crowd Monitoring "Simulated Live Network" section is labelled as a demo.
- **Hourly station data covers 12 Aug – 30 Sep 2025.** Several pages (Dashboard, Crowd Monitoring operations panel) show a fixed historical snapshot for 2025-09-30 at 18:00.
- **2026 demo data is date-shifted historical data**, not actual 2026 observations.
- **Forecasts are model estimates, not observed counts.** Multi-step station forecasts and multi-day demand forecasts are recursive, so errors accumulate with distance. The crowd model's reported metrics apply only to next-hour predictions, and the daily demand model has a modest R² on a small test set.
- **Pressure scores and demand statuses are analytical indicators**, not measured occupancy or confirmed congestion.
- **Scheduling output is decision support only.** Recommended headways come from a heuristic over precomputed analysis. Saved frequency proposals and their Approved/Rejected/Completed status are record-keeping in SQLite and do not change any real timetable. Delay records are manually entered or demo entries; they are not verified delays.
- **Dashboard map is schematic.** It shows up to 12 stations at fixed positions and is not a geographic map.
- **Security is demo-grade.** The JWT secret is written directly in `auth_utils.py` and `routers/auth.py`, and `POST /auth/register` is open. Move the secret to an environment variable and restrict registration before any real deployment.
- **Local setup assumptions.** The backend must be started from the `backend` folder, and the frontend API address is fixed to `http://127.0.0.1:8000`.

---

## 👤 Author

**Mahak Thavrani**: Infosys Springboard Internship
