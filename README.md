# 🚇 MetroFlow: AI-Powered Predictive Crowd Management & Smart Transit Scheduling Platform

MetroFlow is a full-stack transit intelligence system combining an **XGBoost Machine Learning Regressor** with an automated **Smart Scheduling & Overcrowding Alert Engine** and a modern **ReactJS + Vite + Tailwind CSS Frontend** to forecast passenger loads and dispatch optimal train headways in real-time.

> **🔗 Dataset Link:** [Download Master Dataset (Excel Format)](https://docs.google.com/spreadsheets/d/1msXUYKOQ5EbkESvQkFJLWeE7W8WjB6KU/export?format=xlsx)

---

## 🚀 Quick Start Guide

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

```
┌────────────────────────────────────────────────────────┐
│                   ReactJS Frontend                     │
│  (Vite + Tailwind CSS + Lucide + Glassmorphism UI)     │
└──────────────────────────┬─────────────────────────────┘
                           │ REST API / CORS
┌──────────────────────────▼─────────────────────────────┐
│                 FastAPI Backend Server                 │
│              (Port 8000 • CORS Configured)             │
├──────────────────────────┬─────────────────────────────┤
│                          │                             │
│   ┌──────────────────────▼─────────────────────┐       │
│   │   Pre-trained XGBoost Regressor (JSON IO)   │      │
│   │   • 9 Feature Matrix + Cyclical Sin/Cos     │      │
│   │   • 95.06% R² Variance Explanation          │      │
│   └────────────────────────────────────────────┘       │
│                          │                             │
│   ┌──────────────────────▼─────────────────────┐       │
│   │     Automated Rule-Based Scheduling        │       │
│   │   • 🔴 Severe Rush (≥1500 pax) -> 3 Min   │        │
│   │   • 🟡 Moderate (800-1499 pax) -> 6 Min   │        │
│   │   • 🟢 Off-Peak (<800 pax)    -> 10 Min   │        │
│   └────────────────────────────────────────────┘       │
└────────────────────────────────────────────────────────┘
```

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

A recurring daily timetable (≈1,650 services across 4 lines, both directions)
built from the dataset's own observed travel times.

**Network topology** — each line traverses all 5 stations in a different order:

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
   - Inject a delay at any station and watch it cascade downstream.
   - One-click reset of the entire network to baseline.

3. **ML Model Evaluation (`MLInsights.jsx`)**:
   - Hold-out metrics for both regressors, feature importances, residual
     breakdowns by hour and station, and documented methodology.

4. **Live Prediction Calculator (`PredictionCalculator.jsx`)**:
   - Origin & Destination Station Pickers with instant swap.
   - Metro Line Corridor selector.
   - 24-Hour Slider with automatic peak hour indicator.
   - Train Capacity selector.
   - Visual Radial Occupancy Gauge with safety tier color coding.
   - Operational Overcrowding Alert Banner.
   - 1-Click Simulation Scenarios.

5. **Fleet Schedule Advisory Table (`ScheduleAdvisoryTable.jsx`)**:
   - Live schedule directives generated by XGBoost predictions.
   - Real-time search and filtering by traffic tier and lines.

6. **Network Analytics & Model Evaluation (`NetworkAnalytics.jsx`)**:
   - 24-Hour hourly average crowd curve with critical thresholds.
   - Station congestion rankings and line volume breakdown.
   - ML pipeline validation metrics.

---

## 🧹 Data Cleaning, Feature Engineering & ML Pipeline

### ⚙️ Feature Engineering
- **Temporal Extraction:** Hourly breakdown, Day of Week, Rush Hour flag.
- **Cyclical Time Encoding:** $\sin(2\pi \cdot \text{hour}/24)$ and $\cos(2\pi \cdot \text{hour}/24)$.
- **Categorical Encodings:** Label encoded station IDs, lines, and days of week.

### 🤖 Model Training & Accuracy (XGBoost Regressor)
Chronological split (80% Train / 20% Test):
- **$R^2$ Score:** `0.9506` (explains ~95% of passenger count variance).
- **Mean Absolute Error (MAE):** `111.33 passengers` (±9.4% mean deviation, **90.6% precision**).
- **Root Mean Squared Error (RMSE):** `140.60 passengers`.

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
├── docker-compose.yml   # Multi-container orchestration
├── .env                 # Environment configuration
├── frontend/            # React + Vite + Tailwind frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── LiveOpsDashboard.jsx   # Live vs forecast + alerts (default view)
│   │   │   ├── StationCrowdCard.jsx   # Per-station comparison bars
│   │   │   ├── DelaySimulator.jsx     # Timetable, delay register, injection
│   │   │   └── MLInsights.jsx         # Model evaluation dashboard
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
