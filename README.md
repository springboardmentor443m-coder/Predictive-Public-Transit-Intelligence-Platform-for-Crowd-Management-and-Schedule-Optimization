# 🚇 MetroFlow: AI-Powered Predictive Crowd Management & Smart Transit Scheduling Platform

MetroFlow is a full-stack transit intelligence system that **streams live station crowd over a WebSocket** and compares it, second by second, against an **XGBoost** forecast. Where reality outruns the prediction it raises a warning; where trains run late it shows the lateness cascading downstream through a simulated timetable and the crowd compounding on the platform as passengers cannot board.

Two gradient-boosted regressors run side by side — one for passengers *on board*, one for passengers *waiting* — and both are scored on a chronological hold-out split that is never shuffled, so no future information leaks into training.


---

## 🚀 Quick Start Guide

### Option A: One Command (Windows)

```powershell
.\restart.ps1
```

Brings up all three containers, waits for the backend to finish loading its
models and for the frontend to respond, then prints the URLs. It launches
Docker Desktop automatically if the engine is not running, and is safe to run
repeatedly. Variants:

```powershell
.\restart.ps1 -Restart   # force-recreate the containers
.\restart.ps1 -Rebuild   # rebuild images first (slow: ~2GB of downloads)
```

| Service | URL |
|---|---|
| **App** | http://localhost:5173 |
| API | http://localhost:8000 |
| Swagger docs | http://localhost:8000/docs |
| PostgreSQL | `localhost:5432` (`postgres`/`postgres`, db `metroflow`) |

---

### Option A: Local Development (No Docker)

#### 1. Start the FastAPI Backend
```bash
# Install Python dependencies
pip install -r requirements.txt

# Launch FastAPI on port 8000
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```
- **Backend API Live**: `http://localhost:8000`
- **Interactive Swagger Docs**: `http://localhost:8000/docs`

#### 2. Start the ReactJS Frontend
```bash
cd frontend
npm install
npm run dev -- --port 5173
```
- **Frontend Dashboard Live**: `http://localhost:5173`

---

### Option B: Docker Deployment

#### 1. Start Docker Desktop
Make sure Docker Desktop is running (whale icon in system tray).

#### 2. Build and Start All Containers
```bash
docker-compose up --build
```

This starts 3 containers:
- **`db`** — PostgreSQL database on port 5432
- **`backend`** — FastAPI server on port 8000
- **`frontend`** — React dev server on port 5173

#### 3. Verify
```bash
docker ps
docker exec predictive-crowd-schedule-management-and-optimization-db-1 pg_isready -U postgres
```

#### 4. Stop
```bash
docker-compose down
```

---

## 🏗️ System Architecture

Three containers, orchestrated by Docker Compose. The backend is the only
stateful component: it owns the timetable, both models and the simulated clock,
and pushes live frames to the browser over a WebSocket.

```
                    ┌──────────────────────────────────────┐
                    │        Browser  (React 19 + Vite)     │
                    │  6 tabs, each wrapped in ErrorBoundary│
                    └───────┬──────────────────────┬───────┘
                   REST/CORS│                      │ WebSocket
                    (poll fallback)          ws://…/ws/live
                            │                      │
┌───────────────────────────▼──────────────────────▼───────────────────────┐
│                     FastAPI Backend  (port 8000)                       │
│                                                                       │
│  ┌─── live_ops.py ──────────────────────────────────────────────────┐  │
│  │ HistoricalReplay   re-dates the 2023 dataset onto today's       │  │
│  │                    calendar  (same month-day + time-of-day)     │  │
│  │                                                                    │  │
│  │ LiveCrowdEngine    live crowd per station + ML forecast +         │  │
│  │                    deviation warnings; sim clock +1 min/frame     │  │
│  │                                                                    │  │
│  │ TimetableEngine    ~1,650 services/day, 4 lines × 2 directions;   │  │
│  │                    delay injected at one station cascades         │  │
│  │                    downstream, decaying 1 min per leg              │  │
│  │                                                                    │  │
│  │ MLMetrics          chronological 80/20 hold-out evaluation        │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                            │                        │                    │
│  ┌─────────────────────────▼─────────┐  ┌───────────▼────────────────┐  │
│  │ XGBRegressor #1  (shipped)        │  │ XGBRegressor #2 (dashboard)│  │
│  │ metroflow_xgboost_model.json      │  │ metroflow_crowd_model.json │  │
│  │ target: Train_Occupancy_Count     │  │ target:                    │  │
│  │ "passengers ON BOARD"   R² 0.946  │  │ Platform_Crowd_Density     │  │
│  │                                   │  │ "passengers WAITING"       │  │
│  │ 9 features: Entry_Hour,           │  │ R² 0.890                   │  │
│  │ Day_of_Week, Is_Peak_Hour,        │  │                            │  │
│  │ Hour_Sin, Hour_Cos,               │  │                            │  │
│  │ From/To_Station,                   │  │                            │  │
│  │ Line_Color, Train_Capacity         │  │                            │  │
│  └───────────────┬───────────────────┘  └───────────┬────────────────┘  │
│                  │                                  │                   │
│  ┌───────────────▼──────────────────────────────────▼────────────────┐  │
│  │  Headway rule engine:  ≥1500 pax → 3 min │ ≥800 → 6 min │ else 10  │  │
│  └────────────────────────────────────────────────────────────────────┘  │
└───────────────────────────────┬───────────────────────────────────────┘
                                │ async SQLAlchemy (asyncpg)
                    ┌───────────▼────────────┐
                    │  PostgreSQL 16-alpine   │
                    │  users · predictions    │
                    │  (volume: postgres_data)│
                    └────────────────────────┘
```

**Why two models?** The original regressor predicts passengers *on board*. The
live dashboard measures passengers *waiting on the platform*. Comparing one
against the other is meaningless — it produced +95% false alarms. Each live
figure is therefore compared against a forecast of the **same quantity**.

---

## 📡 Live Crowd Operations (Real-Time)

The dashboard's default view streams **live** station crowd over a WebSocket and
compares it against an ML forecast, raising a warning whenever reality outruns
the prediction.

### Where the "live" data comes from
This is **not** invented noise. The master dataset spans **all of 2023**
(2023-01-01 → 2023-12-31, 5,000 trips), so every month/day pair exists. The
engine takes the historical rows matching today's month-day and time-of-day and
re-stamps their calendar with today's date — the time-of-day, station, line,
capacity, delay and crowd columns are preserved verbatim. A simulated clock
then advances one minute per pushed frame, so the numbers on screen genuinely
move while remaining reproducible.

### Live vs Forecast
| Metric | Source |
|---|---|
| **Live crowd** | Re-dated historical `Platform_Crowd_Density`, plus compounding from delay pressure |
| **Forecast crowd** | `metroflow_crowd_model.json` — XGBoost trained on `Platform_Crowd_Density` |
| **Warning** | Fires when live exceeds forecast by ≥ 20% |

> A second model was trained specifically for the dashboard. The originally
> shipped model predicts passengers **on board**, so comparing it against
> platform crowd would be meaningless — each live figure is compared against a
> forecast of the *same quantity*.

---

## 🚆 Train Schedule & Delay Propagation

A recurring daily timetable (≈1,650 services and trains across 4 lines, both directions)
built from the dataset's own observed travel times.

**Network topology** — each line traverses all 5 stations in a different order - Example :

| Line | Route |
|---|---|
| Blue | Dwarka Sec 21 → Botanical Garden → Rajiv Chowk → Kashmere Gate → Hauz Khas |
| Magenta | Botanical Garden → Rajiv Chowk → Kashmere Gate → Hauz Khas → Dwarka Sec 21 |
| Red | Kashmere Gate → Rajiv Chowk → Botanical Garden → Dwarka Sec 21 → Hauz Khas |
| Yellow | Rajiv Chowk → Kashmere Gate → Hauz Khas → Botanical Garden → Dwarka Sec 21 |

### How a delay propagates
Inject a delay at one station and every **downstream** station inherits it,
decaying by 1 minute per leg as the train claws time back. Upstream stations
are untouched.

```
Inject 15 min at Botanical Garden (index 1 of 5):

  Dwarka Sec 21     06:00   delay  0   ON_TIME     <- upstream unaffected
  Botanical Garden  06:09   delay 15   SEVERE     <- origin
  Rajiv Chowk       06:19   delay 14   SEVERE
  Kashmere Gate     06:29   delay 13   SEVERE
  Hauz Khas         06:39   delay 12   SEVERE
```

### Delay → crowd coupling
Lateness means passengers **cannot board**, so platform crowd compounds. The
multiplier scales with how much of a station's timetable is running ≥3 min late
and by how late it is (capped at +85%). Delay every service at Rajiv Chowk by
15 min and the whole network's platform crowd climbs ~50%, tripping CRITICAL
alerts on all five stations. Clearing injections restores the baseline exactly.

### Delay register
Sorted by scheduled departure time, with severity (`MINOR` ≤4 / `MODERATE` ≤9 /
`SEVERE` >9) and the originating station for each late service.

---

## 🧠 Machine Learning

Two gradient-boosted regressors, both scored on the **final 20% of the dataset in
time order** — never shuffled, so no future information leaks into training.

| Model | Target | R² | MAE | RMSE | MAPE |
|---|---|---|---|---|---|
| Occupancy (shipped) | `Train_Occupancy_Count` | **0.946** | 116.09 | 147.40 | 15.26% |
| Platform crowd (dashboard) | `Platform_Crowd_Density` | **0.890** | 91.11 | 118.49 | 22.13% |

**Feature engineering** (9 features): raw hour, cyclical `sin`/`cos` of hour (so
23:00 and 00:00 sit adjacent rather than at opposite ends of the scale),
peak-hour membership, label-encoded station/line/day-of-week, and train
capacity.

**What the models learned:** `Is_Peak_Hour` dominates gain in both models, which
matches the data — crowd is strongly bimodal across the day (≈100 waiting
off-peak vs ≈950 at the evening peak). Midday hours (12:00–16:00) carry the
largest error because demand is both elevated and volatile there. The
`/api/ml/metrics` endpoint reports per-hour and per-station residuals, bias, and
gain-based feature importances.

**Error heatmap (station × hour):** the dashboard renders a colour-scaled grid of
MAE for every station-hour combination, with cells hatched out where the test
split had too few samples to judge honestly. It makes the model's blind spots
obvious at a glance — midday is uniformly the worst band, and the worst single
cell is Rajiv Chowk at 15:00 (MAE ≈ 295).

To retrain the crowd model:

```bash
python train_crowd_model.py
```

---

## 🔌 Live Operations API

| Endpoint | Purpose |
|---|---|
| `WS /ws/live` | Streams a snapshot every 2s |
| `GET /api/live/snapshot` | Single frame (REST fallback) |
| `GET /api/live/network` | Stations, line routes, service window |
| `GET /api/live/station/{name}` | Per-station detail + all delay state |
| `GET /api/schedule/timetable?line=` | Day's services, ordered by departure |
| `GET /api/schedule/delays` | Delay register sorted by time |
| `GET /api/schedule/station/{name}` | Per-train delay at one station |
| `GET /api/schedule/resolve?from_station=&to_station=&line=&hour=` | Resolve a forecast to the actual scheduled service (train id, rake, times, delay chain) |
| `POST /api/schedule/inject-delay` | Cause a delay; watch it propagate |
| `POST /api/schedule/clear-delay/{id}` | Withdraw one train's injections |
| `POST /api/schedule/reset` | Restore the whole network to baseline |
| `POST /api/schedule/simulate?minutes=` | Fast-forward the clock |
| `GET /api/ml/metrics` | Hold-out metrics for both models |
| `GET /api/ml/importances` | Gain-based feature importances |

---

## 🖥️ Frontend Components & Features

1. **Live Crowd Ops (`LiveOpsDashboard.jsx`) — default view**:
   - WebSocket stream of per-station crowd, updating every 2 seconds.
   - Live vs ML-forecast comparison bars on a shared scale.
   - Automatic warning banners when live crowd outruns the forecast by ≥20%,
     with root-cause attribution (delay-driven vs demand surge).
   - Network totals, busiest station, delay-pressure gauges, next services.
   - Automatic fallback to REST polling with exponential-backoff reconnect.

2. **Train Schedule & Delays (`DelaySimulator.jsx`)**:
   - Delay register for every late service, sorted by scheduled departure.
   - Full timetable view with per-stop scheduled vs actual times.
   - Target-service picker with a **live route preview** showing which stations
     will inherit the delay before you commit to it.
   - **Live crowd vs ML forecast for the chosen origin station**, with deviation
     and delay-pressure multiplier, refreshed after every injection.
   - Inject a delay at any station and watch it cascade downstream.
   - One-click reset of the entire network to baseline.

3. **ML Model Evaluation (`MLInsights.jsx` + `ErrorHeatmap.jsx`)**:
   - Hold-out metrics for the shipped occupancy model on a chronological split.
   - Feature-importance bars with a plain-English explainer of what gain means,
     why `Is_Peak_Hour` dominates, and why the near-zero features are a genuine
     finding rather than a bug.
   - **Station x hour error heatmap** with per-station `Actual`, `Predicted` and
     `Samples` roll-up columns, so error figures can be sanity-checked against
     the volumes they came from. Cells with too few samples are hatched out
     rather than shown as a misleading zero.
   - Documented methodology.

4. **Live Prediction Calculator (`PredictionCalculator.jsx` + `ServiceDetails.jsx`)**:
   - Origin & Destination Station Pickers with instant swap.
   - Metro Line Corridor selector.
   - 24-Hour Slider with automatic peak hour indicator.
   - Train Capacity selector.
   - Visual Radial Occupancy Gauge with safety tier color coding.
   - Operational Overcrowding Alert Banner.
   - 1-Click Simulation Scenarios, each revealing the scheduled service it maps to.
   - **Service resolution** - `GET /api/schedule/resolve` matches the chosen
     (origin, destination, line, hour) against today's timetable and names the
     actual train, rake size, scheduled times and delay chain, so it is never
     ambiguous which service a forecast refers to.

5. **Error Boundary (`ErrorBoundary.jsx`)**:
   - Wraps every tab so a single failing view cannot unmount the whole app and
     leave the user staring at a blank page. The navigation stays usable.

6. **Fleet Schedule Advisory Table (`ScheduleAdvisoryTable.jsx`)**:
   - Live schedule directives generated by XGBoost predictions.
   - Real-time search and filtering by traffic tier and lines.

7. **Network Analytics & Model Evaluation (`NetworkAnalytics.jsx`)**:
   - 24-Hour hourly average crowd curve with critical thresholds.
   - Station congestion rankings and line volume breakdown.
   - ML pipeline validation metrics.

---

## 📊 Dataset Overview & Station Metrics

All figures below are computed directly from
`AI_MetroFlow_Master_Dataset.xlsx` (5,000 trip records covering the full year
of 2023) and re-verified against the file.

### 🚉 Passenger Movement by Station

| Station Name | Total Onboarded Passengers | Avg Onboarded per Trip | Total Alighted Passengers | Avg Alighted per Trip |
|---|---:|---:|---:|---:|
| Kashmere Gate | 1,193,511 | ~1,119 | 1,082,973 | ~1,079 |
| Rajiv Chowk | 1,107,892 | ~1,092 | 1,056,008 | ~1,086 |
| Botanical Garden | 1,094,988 | ~1,120 | 1,134,549 | ~1,106 |
| Dwarka Sec 21 | 1,087,041 | ~1,098 | 1,188,686 | ~1,144 |
| Hauz Khas | 1,040,074 | ~1,095 | 1,061,290 | ~1,107 |

- **Highest Onboarding Station:** Kashmere Gate with **1,193,511** passengers.
- **Highest Alighting Station:** Dwarka Sec 21 with **1,188,686** passengers.
- **System Total:** **5,523,506** total passenger movements recorded across all
  trips (the onboarding column and the alighting column each sum to this figure,
  because every trip contributes one boarding and one alighting).

### 1. Max Platform Crowd

The maximum platform crowd recorded in this dataset is **1,199** passengers.

### 2. Max Train Capacity

The maximum train capacity recorded in this dataset is **2,400** passengers.

### 3. Why Only 5,000 Trips & Time Gaps (Headway) Between Trains

**Dataset Scope:** The dataset contains exactly **5,000 total trip records**
logged over a full year (2023). Every trip in the dataset passes through,
starts at, or ends at these stations, making the combined activity count across
the system equal to 5,000 train trips.

**Time Gap (Headway Interval):**

| Metric | Value |
|---|---|
| Average Time Gap | ~4.96 minutes (approx. 5 minutes) |
| Minimum Time Gap | 2 minutes (during peak operational hours) |
| Maximum Time Gap | 14 minutes (during off-peak hours) |

### 4. Why All Stations Appear on Magenta, Red, Blue and Yellow Lines

In this synthetic/simulated dataset, all 4 line colours (Red Line, Blue Line,
Yellow Line and Magenta Line) are assigned across all stations almost equally
(**~1,236 to 1,275 trips per line**).

In real-world geography (Delhi Metro), these stations serve as major
multi-line interchange hubs:

| Station | Real Delhi Metro Lines |
|---|---|
| Kashmere Gate | Red, Yellow and Violet Lines |
| Rajiv Chowk | Blue and Yellow Lines |
| Hauz Khas | Yellow and Magenta Lines |
| Botanical Garden | Blue and Magenta Lines |
| Dwarka Sec 21 | Blue Line and Airport Express |

In this dataset's simplified data model, **every station is modelled as a major
hub capable of connecting all four lines.**

### 5. Station Connections & Interlink Between Dwarka Sec 21 and Botanical Garden

**Layout Structure:** The 5 stations are modelled as a connected network where
trips occur directly between all station pairs in both directions (Up Line and
Down Line).

**Dwarka Sec 21 ↔ Botanical Garden Interlink:** Yes, there are direct routes
between Dwarka Sec 21 and Botanical Garden:

| Direction | Trips |
|---|---:|
| Dwarka Sec 21 → Botanical Garden | 194 |
| Botanical Garden → Dwarka Sec 21 | 188 |

### 6. Dataset Breakdown & Station Metrics

**Station Summary** — there are **5 unique stations** in total in this dataset:

- Botanical Garden
- Dwarka Sec 21
- Hauz Khas
- Kashmere Gate
- Rajiv Chowk

**Total Trains in Dataset**

| Metric | Value |
|---|---|
| Total Trip Records | 5,000 trips |
| Unique Train IDs (`Train_ID`) | 3,829 distinct trains |

**Station-Wise Train Operations (Going & Coming Back)**

| Station Name | Departing Trips (`From_Station`) | Arriving Trips (`To_Station`) | Internal Loop Trips (`From = To`) |
|---|---:|---:|---:|
| Kashmere Gate | 1,067 | 1,004 | 219 |
| Rajiv Chowk | 1,015 | 972 | 204 |
| Dwarka Sec 21 | 990 | 1,039 | 223 |
| Botanical Garden | 978 | 1,026 | 193 |
| Hauz Khas | 950 | 959 | 183 |
| **Total** | **5,000** | **5,000** | **1,022** |

---

## 🧹 Data Cleaning, Feature Engineering & ML Pipeline

### ⚙️ Feature Engineering
- **Temporal Extraction:** Hourly breakdown, Day of Week, Rush Hour flag.
- **Cyclical Time Encoding:** $\sin(2\pi \cdot \text{hour}/24)$ and $\cos(2\pi \cdot \text{hour}/24)$.
- **Categorical Encodings:** Label encoded station IDs, lines, and days of week.

### 🤖 Model Training & Accuracy (XGBoost Regressor)

Both models are scored on the **final 20% of the dataset taken in time order** -
the split is never shuffled, so no future information leaks into training.
These are the figures `/api/ml/metrics` actually returns from a live refit on
the 80% training split:

| Model | Target | $R^2$ | MAE | RMSE | MAPE |
|---|---|---|---|---|---|
| Occupancy (shipped) | `Train_Occupancy_Count` | **0.9457** | 116.09 | 147.40 | 15.26% |
| Platform crowd (dashboard) | `Platform_Crowd_Density` | **0.8895** | 91.11 | 118.49 | 22.13% |

- **$R^2$ Score:** `0.9457` - explains ~95% of passenger-count variance.
- **Mean Absolute Error:** `116.09 passengers`; **52.9%** of predictions land
  within ±10% of the true figure.
- **Root Mean Squared Error:** `147.40 passengers`.
- **Bias:** `-2.2` passengers, i.e. essentially unbiased overall.

Retrain the dashboard model with `python train_crowd_model.py`.

---

## 🚦 Smart Scheduling Rule Engine

| Traffic Tier | Predicted Occupancy | Recommended Headway | Automated Fleet Action |
|---|---|---|---|
| 🔴 **Severe Rush Hour** | $\ge 1,500$ pax | **3 Minutes** | High-Frequency Dispatch |
| 🟡 **Moderate Traffic** | $800 - 1,499$ pax | **5–6 Minutes** | Maintain Standard Headway |
| 🟢 **Off-Peak Flow** | $< 800$ pax | **10 Minutes** | Extend Headway (Conserve Fleet) |

---

## 🐘 Database & Auth

- **PostgreSQL** with SQLAlchemy async engine + `asyncpg`
- **JWT Authentication** with `python-jose` + `bcrypt` password hashing
- **Default Admin**: `admin` / `admin123`
- **Endpoints**: `/api/auth/login`, `/api/auth/register`, `/api/auth/me`, `/api/predict`, `/api/schedule-advisory`, `/api/analytics`, `/api/meta`, `/health`

---

## 📁 Project Structure

```
MetroFlow/
├── main.py              # FastAPI backend server (all endpoints)
├── live_ops.py          # Live crowd engine, timetable, delay propagation, ML metrics
├── train_crowd_model.py # Trains the platform-crowd regressor
├── database.py          # PostgreSQL models & async functions
├── auth.py              # JWT auth with bcrypt password hashing
├── requirements.txt     # All Python dependencies
├── Dockerfile           # Backend Docker image
├── docker-compose.yml   # Multi-container orchestration (db + backend + frontend)
├── restart.ps1          # One-command start / restart helper
├── .env                 # Environment configuration (git-ignored)
├── frontend/            # React + Vite + Tailwind frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── LiveOpsDashboard.jsx   # Live vs forecast + alerts (default view)
│   │   │   ├── StationCrowdCard.jsx   # Per-station comparison bars
│   │   │   ├── DelaySimulator.jsx     # Timetable, delay register, injection
│   │   │   ├── MLInsights.jsx         # Model evaluation dashboard
│   │   │   ├── ErrorHeatmap.jsx       # Station x hour error heatmap
│   │   │   ├── ServiceDetails.jsx     # Which train a forecast refers to
│   │   │   └── ErrorBoundary.jsx      # Contains a failing view to one panel
│   │   ├── hooks/useLiveSocket.js     # WebSocket + polling fallback
│   │   ├── services/    # API service layer
│   │   └── App.jsx      # Main App component
│   ├── Dockerfile       # Frontend Docker image
│   └── package.json
├── metroflow_xgboost_model.json      # Occupancy model (on board)
├── metroflow_crowd_model.json        # Platform-crowd model (dashboard)
├── metroflow_crowd_metrics.json      # Crowd model eval metrics
├── AI_MetroFlow_Master_Dataset.xlsx  # Training dataset (5,000 trips, 2023)
├── README.md
└── DOCUMENTATION.md
```

---

## 📋 Requirements

- **Python 3.11+**
- **Node.js 20+**
- **Docker & Docker Compose** (for containerized deployment)
- **PostgreSQL 16** (for production)

### Python Dependencies
```
fastapi, uvicorn[standard], pandas, numpy, xgboost, scikit-learn
openpyxl, pydantic, joblib, passlib[cryptography], psycopg2-binary
sqlalchemy[asyncio], aiosqlite, asyncpg, python-multipart
python-jose[cryptography], bcrypt<4, python-dotenv
```
WebSocket support ships with `uvicorn[standard]` (the `websockets` package).

---

## 📄 License
This project is licensed under the MIT License.
