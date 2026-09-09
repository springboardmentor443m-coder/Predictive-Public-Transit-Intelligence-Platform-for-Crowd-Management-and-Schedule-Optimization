<div align="center">

# 🚇 MetroFlow: Predictive Public Transit Intelligence Platform
### *AI-Driven Platform Crowd Management & Dynamic Schedule Optimization*

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110.0-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-14.2-black?logo=next.js&logoColor=white)](https://nextjs.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.2-EE4C2C?logo=pytorch&logoColor=white)](https://pytorch.org/)
[![XGBoost](https://img.shields.io/badge/XGBoost-2.0-eb6024?logoColor=white)](https://xgboost.readthedocs.io/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![Tests: 11 Passed](https://img.shields.io/badge/Pytest-11%20Passed-success?logo=pytest&logoColor=white)](https://pytest.org/)

<p align="center">
  <b>MetroFlow</b> is an enterprise-grade, real-time public transit intelligence platform built for metro rail networks and rapid transit operators. It fuses multi-horizon machine learning models (XGBoost, PyTorch LSTM), real-time turnstile telemetry, and automated dispatch controls to mitigate platform overcrowding, detect network anomalies, and dynamically optimize train headways.
</p>

[Key Features](#key-features) • [System Architecture](#system-architecture) • [Modules & Pages](#core-modules--pages) • [Real-World Datasets](#real-world-dataset-pipeline) • [Quick Start](#quick-start-local-execution) • [Docker Compose](#docker-compose-orchestration) • [API Reference](#api-reference) • [Testing](#running-automated-tests)

</div>

---

## 🌟 Key Features

- 🛰️ **Real-Time Platform Density Telemetry**: Live station inflow/outflow passenger-per-minute (PPM) monitoring and platform occupancy gauges streaming over low-latency WebSockets (`/ws/live`).
- 🧠 **Multi-Horizon AI Demand Forecasting**: Station-level passenger demand projections for 15, 30, and 60-minute horizons powered by trained **XGBoost Regressors** with 95% confidence intervals.
- 🚨 **Congestion & Anomaly Detection**: Deep-learning **PyTorch LSTM** autoencoders paired with Random Forest classifiers detecting surge anomalies and bottleneck risks before overcrowding cascades.
- 🚊 **Dynamic Schedule & Headway Optimization**: Automated dispatch recommendation engine that recalculates train frequencies based on real-time load, backed by an operator override cockpit with hard safety constraints (`headway ≥ 3 min`).
- 🌐 **Heterogeneous Transit Dataset Importers**: Built-in data ingestion pipelines for international open transit datasets including **NYC MTA Turnstiles**, **Seoul Metro**, **Transport for London (TfL)**, and **Deutsche Bahn (DB)** delay logs.
- 📢 **Operations Alert & Dispatch Center**: Automated threshold triggers (`Density > 80%`, signal delays) and one-click multi-station Public Address (PA) and SMS alert broadcasts.
- 📊 **Executive Analytics & Reporting**: Historical 24-hour passenger throughput curves, On-Time Performance (OTP %) breakdowns by transit line, and one-click CSV report exports.

---

## 🏗️ System Architecture

```mermaid
flowchart TB
    subgraph Frontend ["Frontend (Next.js 14 / TypeScript)"]
        UI["Executive Dashboard & Control Cockpit\n(Tailwind CSS + Recharts + Lucide)"]
        WS_Client["WebSocket Live Client\n(/ws/live)"]
        REST_Client["Axios / Fetch API Client\n(/api/v1/*)"]
    end

    subgraph Backend ["Backend API & Orchestration (FastAPI)"]
        FastAPI_App["FastAPI Application Gateway"]
        WS_Manager["WebSocket Telemetry Broadcaster"]
        Auth_Router["JWT Auth & RBAC (/auth)"]
        Crowd_Router["Crowd Monitoring (/crowd)"]
        Sched_Router["Schedules & Dispatch (/schedules)"]
        Pred_Router["AI Predictions (/predictions)"]
        Alert_Router["Alerts & PA Dispatch (/alerts)"]
        Data_Router["Datasets & Retraining (/datasets)"]
    end

    subgraph AI_Engine ["AI & Machine Learning Engine"]
        XGB["XGBoost Demand Forecaster\n(15m, 30m, 60m Horizons)"]
        LSTM["PyTorch LSTM Network\n(Anomaly & Congestion Risk)"]
        Pipelines["Data Normalization Pipeline\n(NYC MTA, Seoul, TfL, DB)"]
    end

    subgraph Storage ["Databases & Cache Layer"]
        PG[("PostgreSQL / SQLite Fallback\nRelational Stations, Schedules & Users")]
        Mongo[("MongoDB\nTelemetry Event Logs & Sensor Data")]
        Redis_Store[("Redis\nPub/Sub & Density State Caching")]
    end

    UI --> REST_Client
    UI --> WS_Client
    REST_Client --> FastAPI_App
    WS_Client <--> WS_Manager

    FastAPI_App --> Auth_Router
    FastAPI_App --> Crowd_Router
    FastAPI_App --> Sched_Router
    FastAPI_App --> Pred_Router
    FastAPI_App --> Alert_Router
    FastAPI_App --> Data_Router

    Pred_Router --> XGB
    Pred_Router --> LSTM
    Data_Router --> Pipelines
    Pipelines --> XGB
    Pipelines --> LSTM

    Crowd_Router --> Storage
    Sched_Router --> Storage
    Alert_Router --> Storage
    FastAPI_App --> Storage
```

---

## 💻 Tech Stack

| Layer | Technologies |
|---|---|
| **Frontend UI** | Next.js 14 (App Router), React 18, TypeScript, Tailwind CSS, Recharts, Lucide React |
| **Backend API** | Python 3.11+, FastAPI, Uvicorn, Pydantic v2, SQLAlchemy 2.0 (Asyncio), WebSockets |
| **Machine Learning** | PyTorch, XGBoost, Scikit-learn, Pandas, NumPy, Joblib |
| **Databases** | PostgreSQL (`asyncpg`), MongoDB (`motor`), Redis, with automatic local SQLite & in-memory failover |
| **DevOps & Testing** | Docker, Docker Compose, Pytest, Pytest-asyncio, HTTPX |

---

## 🗂️ Project Structure

```
metroflow/
├── docker-compose.yml              # Multi-container orchestration (FastAPI, Next.js, Postgres, Mongo, Redis)
├── README.md                       # Project documentation
│
├── backend/                        # FastAPI Backend Application
│   ├── Dockerfile                  # Production container build
│   ├── pytest.ini                  # Pytest configuration
│   ├── requirements.txt            # Python dependencies
│   ├── tests/                      # Automated test suite (11 test cases)
│   │   ├── test_auth.py            # JWT token & user verification tests
│   │   ├── test_crowd.py           # Density calculations & summary tests
│   │   ├── test_datasets.py        # Pipeline ingestion & retrain tests
│   │   ├── test_predictions.py     # AI inference & horizon tests
│   │   └── test_schedules.py       # Schedule override & safety limit tests
│   └── app/
│       ├── main.py                 # FastAPI application entrypoint & WebSocket broadcaster
│       ├── api/v1/                 # Modular API route controllers
│       │   ├── api_router.py       # Central router aggregation
│       │   └── endpoints/          # Route handlers (auth, crowd, schedules, predictions, alerts, datasets)
│       ├── core/                   # Security, JWT, configuration & database session management
│       ├── datasets/               # Real-world transit dataset pipelines & importers
│       │   ├── pipeline.py         # Multi-source dataset ingestion orchestrator
│       │   ├── importers/          # MTA, Seoul Metro, TfL, DB custom parsers
│       │   ├── raw/                # Sample raw transit data files
│       │   └── processed/          # Standardized master CSV & Parquet files
│       ├── ml/                     # ML training scripts and serialized model artifacts
│       │   ├── train_demand_model.py
│       │   ├── train_crowd_model.py
│       │   └── saved_models/       # .joblib & .pt model binaries
│       ├── models/                 # SQLAlchemy ORM models
│       ├── schemas/                # Pydantic validation schemas
│       └── services/               # Core business logic services
│
└── frontend/                       # Next.js 14 Frontend Application
    ├── Dockerfile                  # Node.js production container build
    ├── package.json                # Dependencies & npm scripts
    ├── tailwind.config.js          # Tailwind styling configuration
    └── src/
        ├── app/                    # Next.js App Router pages
        │   ├── (auth)/             # Login & Registration flows
        │   ├── dashboard/          # Executive KPI overview & SVG network map
        │   ├── live-monitoring/    # Real-time platform crowd density grid
        │   ├── predictions/        # Multi-horizon forecasting & optimization
        │   ├── schedules/          # Train timetable & headway override controls
        │   ├── alerts/             # Active alerts feed & PA broadcast modal
        │   ├── analytics/          # 24h throughput & OTP performance charts
        │   └── datasets/           # External dataset ingestion & retraining hub
        ├── components/             # Reusable UI widgets & layout wrappers
        ├── lib/                    # API client abstraction & utility helpers
        └── types/                  # TypeScript interface definitions
```

---

## 🖥️ Core Modules & Pages

| Route | Module Name | Primary Functions |
|---|---|---|
| `/dashboard` | **Executive Overview** | System KPIs (active trains, system-wide PPM, OTP rate, active alerts) and interactive SVG Metro Network Map (Red & Blue lines). |
| `/live-monitoring` | **Live Crowd Monitoring** | Station-by-station telemetry cards, platform density gauges, inflow/outflow balance, and real-time status badges (Normal, Busy, Critical). |
| `/predictions` | **AI Forecast & Insights** | Multi-horizon passenger demand curves (15m, 30m, 60m), 95% confidence intervals, and automated frequency recommendations. |
| `/schedules` | **Schedule & Dispatch Manager** | Live timetable, delay propagation indicators, dynamic optimization cards, and manual headway override controls with validation. |
| `/alerts` | **Alerts & Operations Center** | Real-time threshold alerts (Overcrowding > 80%, Line delays), alert resolution workflow, and targeted PA/SMS announcement broadcast tool. |
| `/analytics` | **Analytics & Reports** | 24-hour station throughput charts, peak-hour load comparison, line-by-line On-Time Performance (OTP) breakdown, and CSV report export. |
| `/datasets` | **Real-World Datasets Hub** | Ingest raw datasets from NYC MTA, Seoul Metro, TfL, and Deutsche Bahn; triggers model retraining with updated $R^2$ and MAE scores. |

---

## 🌍 Real-World Dataset Pipeline

MetroFlow includes a robust data integration pipeline that converts real-world open transit datasets into standardized inflow/outflow telemetry:

- **NYC MTA Turnstiles:** Parses turnstile counter diffs across 4-hour windows and transforms them into 15-minute station passenger rates.
- **Seoul Metro:** Standardizes hourly boarding and alighting volumes across Lines 1–9.
- **Transport for London (TfL):** Ingests smartcard tap-in/tap-out JSON records for London Underground stations.
- **Deutsche Bahn (DB):** Integrates delay minutes, incident codes, and route disruptions into station operational metrics.

```bash
# Ingest raw external datasets into standardized master dataset (CSV & Parquet)
cd backend
$env:PYTHONPATH="."
python app/datasets/pipeline.py
```

---

## 🚀 Quick Start (Local Execution)

### Prerequisites
- **Python:** 3.11 or higher
- **Node.js:** 18.x or higher
- **Git**

---

### 1. Clone the Repository

```bash
git clone https://github.com/springboardmentor443m-coder/Predictive-Public-Transit-Intelligence-Platform-for-Crowd-Management-and-Schedule-Optimization.git
cd Predictive-Public-Transit-Intelligence-Platform-for-Crowd-Management-and-Schedule-Optimization
```

---

### 2. Backend Setup & AI Model Training

```bash
cd backend

# Create and activate a virtual environment
python -m venv venv

# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Linux / macOS:
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt email-validator

# Train the AI forecasting & anomaly detection models
$env:PYTHONPATH="."          # On Linux/macOS: export PYTHONPATH="."
python app/ml/train_demand_model.py
python app/ml/train_crowd_model.py

# Start the FastAPI server with live reload
uvicorn app.main:app --reload --port 8000
```

- **Interactive API Documentation (Swagger UI):** `http://localhost:8000/docs`
- **Alternative ReDoc UI:** `http://localhost:8000/redoc`
- **Live WebSocket Stream:** `ws://localhost:8000/ws/live`

---

### 3. Frontend Setup

In a separate terminal window:

```bash
cd frontend

# Install Node dependencies
npm install

# Start the Next.js development server
npm run dev
```

- **Web Application Cockpit:** `http://localhost:3000`

---

## 🐳 Docker Compose Orchestration

To run the complete production-like stack including **FastAPI**, **Next.js**, **PostgreSQL**, **MongoDB**, and **Redis** with a single command:

```bash
docker-compose up --build
```

### Container Endpoints:
| Container | Service | Port Binding |
|---|---|---|
| `frontend` | Next.js 14 Dashboard | `http://localhost:3000` |
| `backend` | FastAPI Gateway & WebSockets | `http://localhost:8000` |
| `postgres` | PostgreSQL Database | `localhost:5432` |
| `mongo` | MongoDB Event Log Store | `localhost:27017` |
| `redis` | Redis Cache & Pub/Sub | `localhost:6379` |

To tear down the containers:
```bash
docker-compose down -v
```

---

## 🧪 Running Automated Tests

MetroFlow features an automated test suite covering authentication, crowd calculations, real-world dataset pipelines, AI model inference, and schedule headway overrides:

```bash
cd backend
$env:PYTHONPATH="."          # On Linux/macOS: export PYTHONPATH="."
python -m pytest tests -v
```

### Verified Test Suite Summary:
```
tests/test_auth.py ........ [PASS] JWT authentication & user profile
tests/test_crowd.py ....... [PASS] Platform density calculation & station telemetry
tests/test_datasets.py .... [PASS] Dataset ingestion pipeline & ML retrain triggers
tests/test_predictions.py . [PASS] 15/30/60-min horizon forecasting & confidence bounds
tests/test_schedules.py ... [PASS] Train timetable & 3-minute headway safety constraints
======================= 11 passed in ~16s =======================
```

---

## 📡 API Reference

### Authentication
- `POST /api/v1/auth/register` — Register a new operations officer or station master.
- `POST /api/v1/auth/login` — Authenticate and receive JWT access & refresh tokens.
- `GET /api/v1/auth/me` — Fetch current user context and permissions.

### Crowd Density & Telemetry
- `GET /api/v1/crowd/summary` — Network-wide overview (total passengers, high-density stations).
- `GET /api/v1/crowd/densities` — Real-time list of all stations with inflow/outflow PPM.
- `GET /api/v1/crowd/station/{station_id}` — Detailed telemetry for a specific station.

### Dynamic Schedules & Dispatch
- `GET /api/v1/schedules/` — Active train schedules, lines, and delay states.
- `GET /api/v1/schedules/optimizations` — AI-generated headway recommendations.
- `POST /api/v1/schedules/override` — Manually override train headway (enforces `≥ 3 min` safety limit).

### AI Demand Forecasting
- `GET /api/v1/predictions/forecast/{station_id}?horizon=30` — ML demand curve with confidence intervals.
- `GET /api/v1/predictions/all?horizon=30` — Network-wide station demand forecasts.
- `GET /api/v1/predictions/anomalies` — List detected crowd surge anomalies.

### Operations & Alerts
- `GET /api/v1/alerts/` — Active and historical alerts feed.
- `POST /api/v1/alerts/broadcast` — Broadcast PA announcement or SMS alert.
- `POST /api/v1/alerts/resolve/{alert_id}` — Mark an alert as resolved.

### Real-World Datasets
- `GET /api/v1/datasets/stats` — Ingested records count, sources, and ML model performance metrics.
- `POST /api/v1/datasets/ingest` — Ingest & normalize raw transit datasets.
- `POST /api/v1/datasets/retrain` — Retrain XGBoost & PyTorch models on the unified dataset.

### WebSockets
- `ws://localhost:8000/ws/live` — Bi-directional telemetry feed broadcasting live crowd metrics every 3 seconds.

---

## ⚙️ Environment Configuration

### Backend (`backend/.env`)
```env
PROJECT_NAME="MetroFlow Intelligence Platform"
API_V1_STR="/api/v1"
SECRET_KEY="replace_with_a_secure_jwt_secret_key"
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Database connections (defaults automatically fallback to local SQLite if unset)
DATABASE_URL="sqlite+aiosqlite:///./metroflow.db"
SYNC_DATABASE_URL="sqlite:///./metroflow.db"
# For production PostgreSQL:
# DATABASE_URL="postgresql+asyncpg://metroflow:metroflow_pass@localhost:5432/metroflow_db"

MONGODB_URL="mongodb://localhost:27017"
REDIS_URL="redis://localhost:6379/0"
```

### Frontend (`frontend/.env.local`)
```env
NEXT_PUBLIC_API_URL="http://localhost:8000/api/v1"
NEXT_PUBLIC_WS_URL="ws://localhost:8000/ws/live"
```

---

## 🚢 Pushing Updates to GitHub

To commit and push all recent changes, models, and documentation to your GitHub repository:

```bash
# 1. Review status of modified and untracked files
git status

# 2. Stage all modifications (code, models, datasets, docs)
git add .

# 3. Commit with a structured message
git commit -m "docs: update README with architecture, dataset pipeline, and deployment guide"

# 4. Push to your active branch (e.g. varun-kumar or main)
git push origin varun-kumar
```

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

<div align="center">
  <b>MetroFlow Transit Intelligence</b> • Built for safer, smarter, and more resilient urban mobility.
</div>
