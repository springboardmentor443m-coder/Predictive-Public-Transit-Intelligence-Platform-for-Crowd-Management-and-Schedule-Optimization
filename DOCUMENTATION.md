# MetroFlow: AI-Powered Metro Crowd Management & Scheduling Platform

## Documentation

### Version 1.0
### Last Updated: September 2026

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [System Architecture](#2-system-architecture)
3. [Modules Implemented](#3-modules-implemented)
4. [Technical Stack](#4-technical-stack)
5. [How Each Module Was Implemented](#5-how-each-module-was-implemented)
6. [API Endpoints](#6-api-endpoints)
7. [Database Schema](#7-database-schema)
8. [Deployment & Docker](#8-deployment--docker)
9. [Known Issues & Next Steps](#9-known-issues--next-steps)

---

## 1. Project Overview

MetroFlow is an AI-powered metro crowd management and scheduling platform that helps metro authorities monitor passenger flow, predict crowd density, and optimize train scheduling in real time.

**Core Idea**: Passengers make a prediction (station pair + time → predicted occupancy), and the system automatically recommends schedule adjustments (headway, rake formation) based on that prediction.

**Key Innovation**: When you predict crowd density for a station pair, the system automatically filters and shows ALL trains on that corridor with updated schedule recommendations — the prediction drives the schedule advisory.

---

## 2. System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    REACT FRONTEND                        │
│              (Vite + React + Tailwind CSS)               │
│                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐  │
│  │ Prediction│  │ Schedule │  │  Network Analytics   │  │
│  │ Calculator│  │ Advisory │  │  Dashboard           │  │
│  └────┬─────┘  └────┬─────┘  └──────────┬───────────┘  │
│       │              │                   │               │
│       └──────┬───────┘                   │               │
│              ▼                           │               │
│  ┌─────────────────────────────────────────────┐       │
│  │         API CLIENT (api.js)                 │       │
│  └────────────────────┬────────────────────────┘       │
└───────────────────────┼────────────────────────────────┘
                        │ HTTP (port 5173)
                        ▼
┌─────────────────────────────────────────────────────────┐
│                    FASTAPI BACKEND                       │
│              (Python + Uvicorn)                          │
│                                                          │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │ XGBoost      │  │  Auth System │  │  Database     │  │
│  │ Prediction   │  │  (JWT+bcrypt)│  │  (SQLite)     │  │
│  │ Engine       │  │              │  │               │  │
│  └──────┬──────┘  └──────────────┘  └───────────────┘  │
│         │                                               │
│         ▼                                               │
│  ┌──────────────────────────────────────────────────┐   │
│  │         main.py (All Routes)                     │   │
│  │  - /api/predict      - Prediction Engine         │   │
│  │  - /api/schedule-    - Prediction-driven Advisory│   │
│  │    advisory                                   │   │
│  │  - /api/analytics    - Dashboard Data            │   │
│  │  - /api/auth/*     - Authentication             │   │
│  │  - /health           - Health Check               │   │
│  └──────────────────────────────────────────────────┘   │
└───────────────────────┬────────────────────────────────┘
                        │ HTTP (port 8000)
                        ▼
┌─────────────────────────────────────────────────────────┐
│                    DATABASE (SQLite)                     │
│            metroflow_predictions.db                      │
│                                                          │
│  Tables: predictions, users                              │
└─────────────────────────────────────────────────────────┘
```

---

## 3. Modules Implemented

### Module 1: User Management
| Feature | Status | Implementation |
|---------|--------|----------------|
| Admin/Operator Login | ✅ | JWT-based authentication with bcrypt password hashing |
| Role-Based Access Control | ✅ | `role` field in User model (admin/user) |
| Default Admin Account | ✅ | Auto-created on first startup (`admin`/`admin123`) |
| Registration | ✅ | `/api/auth/register` endpoint |

**Criteria**: Authentication uses `bcrypt<4` for password hashing (not passlib, which is incompatible with Python 3.14). JWT tokens (HS256) expire in 24 hours. `ensure_default_admin()` creates the default admin on first run.

---

### Module 2: Crowd Monitoring
| Feature | Status | Implementation |
|---------|--------|----------------|
| Real-time Passenger Density | ✅ | XGBoost model predicts occupancy from station pair + time |
| Occupancy Gauge | ✅ | Frontend gauge component showing predicted density |
| Alert System | ✅ | CRITICAL/MODERATE/NORMAL alert levels based on occupancy |
| Heatmap Generation | ⚠️ | Planned but not fully implemented |

**Criteria**: XGBoost Regressor achieves R²=95.06% accuracy. Input features: Entry_Hour, Day_of_Week, Is_Peak_Hour, Hour_Sin, Hour_Cos, From_Station, To_Station, Line_Color, Train_Capacity. Prediction output: occupancy count → traffic tier → alert level.

---

### Module 3: Scheduling Management
| Feature | Status | Implementation |
|---------|--------|----------------|
| Schedule Advisory | ✅ | Dynamic: prediction drives which trains are shown |
| Headway Optimization | ✅ | 3-min (severe), 6-min (moderate), 10-min (off-peak) |
| Fleet Action Recommendations | ✅ | 8-coach, 6-coach, 4-coach rake formation suggestions |
| Line/Corridor Filtering | ✅ | Prediction filters trains by line, station pair, hour |

**Criteria**: This is the KEY innovation. When you predict 2149 passengers from Botanical Garden → Dwarka Sec 21 at 17:00, the schedule advisory automatically filters and shows ALL trains on that line/corridor with updated schedules. The `/api/schedule-advisory` endpoint accepts `from_station`, `to_station`, `line`, `hour` query parameters and dynamically filters the dataset.

**Implementation Flow**:
```
PredictionCalculator.predict() → setPredictionParams() → ScheduleAdvisoryTable.useEffect() → fetchScheduleAdvisory(params) → Backend filters dataset → Returns prediction_based: True
```

---

### Module 4: AI Prediction
| Feature | Status | Implementation |
|---------|--------|----------------|
| XGBoost Model | ✅ | Pre-trained model at `metroflow_xgboost_model.json` |
| Real-time Inference | ✅ | `/api/predict` endpoint returns occupancy + recommendations |
| Traffic Tier Classification | ✅ | SEVERE_RUSH (≥1500), MODERATE (800-1499), OFF_PEAK (<800) |
| Capacity Rake Analysis | ✅ | 2400/1800/1500 pax capacity recommendations |

**Criteria**: XGBoost model trained on 5000 rows (2023 dataset). Features are cyclical (sin/cos encoding for hours). Auto-computes peak hour flags. Model loaded via native JSON format.

---

### Module 5: Alert & Notification
| Feature | Status | Implementation |
|---------|--------|----------------|
| Overcrowding Alerts | ✅ | CRITICAL/MODERATE/NORMAL tiers |
| Delay Notifications | ✅ | `alert_status` in prediction response |
| Real-time Updates | ✅ | Vite hot-reload for frontend, uvicorn auto-reload for backend |
| Alert Banner | ✅ | Frontend `AlertBanner` component |

**Criteria**: Alert triggered by `trigger_overcrowding_alert()` function based on prediction vs train capacity. CRITICAL if ≥1500 passengers, MODERATE if ≥800, NORMAL otherwise.

---

### Module 6: Analytics Dashboard
| Feature | Status | Implementation |
|---------|--------|----------------|
| Station Performance | ✅ | `NetworkAnalytics.jsx` shows KPIs |
| Traffic Tier Counts | ✅ | SEVERE_RUSH/MODERATE/OFF_PEAK counts |
| Operational Monitoring | ✅ | Backend health status, metadata display |
| AI Prediction Insights | ✅ | Prediction-based schedule advisory |

**Criteria**: Dashboard fetches from `/api/analytics` and `/api/meta` endpoints. Shows station counts, tier distribution, and system health.

---

### Module 7: Data Sources
| Feature | Status | Implementation |
|---------|--------|----------------|
| Dataset (2023) | ✅ | 5000 rows, 19 columns |
| 2020-2027 Data | ❌ | Currently only 2023 data available |
| Dataset Format | Excel (.xlsx) | `AI_MetroFlow_Master_Dataset.xlsx` |

**Criteria**: Current dataset covers 2023 only. Mentor requires 2020-2027 data. This is the #1 blocker for full project completion.

---

## 4. Technical Stack

| Layer | Technology | Details |
|-------|-----------|---------|
| **Frontend** | React 18 + Vite + Tailwind CSS | TypeScript-free (plain JS), Lucide icons |
| **Backend** | FastAPI + Uvicorn | Python 3.14, auto-reload |
| **ML Model** | XGBoost | Pre-trained JSON model |
| **Database** | SQLite + SQLAlchemy | Async, auto-initialized on startup |
| **Auth** | JWT (jose) + bcrypt | HS256 tokens, 24hr expiry |
| **Container** | Docker + docker-compose | Docker Desktop not currently running |
| **API Docs** | Swagger UI | Auto-generated at `/docs` |

---

## 5. How Each Module Was Implemented

### Prediction-to-Schedule Pipeline (Key Flow)

```
User selects: Station A → Station B, 18:00, Friday
         ↓
PredictionCalculator.handlePredict()
         ↓
POST /api/predict (XGBoost model)
         ↓
Response: {predicted_occupancy: 2149, alert: CRITICAL, headway: 3min}
         ↓
PredictionCalculator calls:
  - setPredictionParams({from_station: "Botanical Garden", to_station: "Dwarka Sec 21", line: "Blue Line", hour: 17})
  - fetchScheduleAdvisory(params)
         ↓
ScheduleAdvisoryTable receives predictionParams via props
         ↓
useEffect triggers: loadData(predictionParams)
         ↓
GET /api/schedule-advisory?from_station=Botanical+Garden&to_station=Dwarka+Sec+21&line=Blue+Line&hour=17
         ↓
Backend filters dataset for matching trains
         ↓
Response: {total_records_analyzed: 100, prediction_based: True, directives: [...], filter: {...}}
         ↓
Frontend shows purple "AI-Powered" badge + filtered trains
```

### Key Files and Their Roles

| File | Purpose |
|------|---------|
| `main.py` | FastAPI server, all routes, XGBoost inference |
| `auth.py` | JWT auth with bcrypt, `ensure_default_admin()` |
| `database.py` | SQLite + SQLAlchemy models and functions |
| `frontend/src/App.jsx` | Root component, predictionParams state |
| `frontend/src/components/PredictionCalculator.jsx` | Prediction UI, calls `setPredictionParams()` |
| `frontend/src/components/ScheduleAdvisoryTable.jsx` | Schedule advisory, auto-loads on prediction params |
| `frontend/src/services/api.js` | API client, `fetchScheduleAdvisory(params)` |
| `frontend/src/components/NetworkAnalytics.jsx` | Dashboard KPIs |
| `frontend/src/components/AlertBanner.jsx` | Alert notifications |
| `frontend/src/components/OccupancyGauge.jsx` | Occupancy visualization |

---

## 6. API Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/health` | Health check | No |
| GET | `/` | Root metadata | No |
| GET | `/api/meta` | Metro network metadata (stations, lines) | No |
| POST | `/api/predict` | Predict occupancy for station pair | No |
| GET | `/api/schedule-advisory` | Schedule advisory (filtered by params) | No |
| GET | `/api/analytics` | Analytics data | No |
| POST | `/api/auth/login` | Login and get JWT token | No |
| POST | `/api/auth/register` | Register new user | No |
| GET | `/api/auth/me` | Get current user profile | Yes (JWT) |

**Removed Endpoints** (per mentor: no historical data):
- ❌ `/api/auth/history` — removed
- ❌ `/api/auth/stats` — removed

---

## 7. Database Schema

### `predictions` table
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| from_station | TEXT | Origin station name |
| to_station | TEXT | Destination station name |
| line_color | TEXT | Metro line name |
| entry_hour | INTEGER | Hour of day |
| day_of_week | TEXT | Day name |
| train_capacity | INTEGER | Train capacity |
| predicted_occupancy | FLOAT | XGBoost prediction |
| occupancy_rate_pct | FLOAT | Occupancy percentage |
| recommended_headway | INTEGER | Recommended headway (min) |
| traffic_tier | TEXT | SEVERE_RUSH/MODERATE/OFF_PEAK |
| fleet_action | TEXT | Recommended action |
| alert_level | TEXT | CRITICAL/MODERATE/NORMAL |
| created_at | DATETIME | Timestamp |

### `users` table
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| username | TEXT | Unique username |
| password_hash | TEXT | bcrypt hashed password |
| role | TEXT | admin/user |
| is_active | BOOLEAN | Active status |

---

## 8. Deployment & Docker

### Docker Setup
Files created:
- `Dockerfile` — Multi-stage build (Python + Node)
- `docker-compose.yml` — Backend + Frontend services
- `DOCKER_SETUP.md` — Deployment guide

**Current Status**: Docker Desktop not running on this machine. To deploy:
```bash
docker-compose up -d --build
```

### Local Development
```bash
# Terminal 1: Backend
cd metroflow-backend
python -m uvicorn main:app --reload --port 8000

# Terminal 2: Frontend
cd metroflow-backend/frontend
npm run dev -- --port 5173
```

---

## 9. Known Issues & Next Steps

### Blockers
1. **Dataset Year**: Only 2023 data available. Mentor requires 2020-2027.
2. **Docker Desktop**: Not installed/running on this machine.
3. **Frontend node_modules**: Missing initially, installed via `npm install`.

### Remaining Work
1. **Get 2020-2027 dataset** — Replace current 2023-only dataset
2. **Start Docker** — Install Docker Desktop, then `docker-compose up -d --build`
3. **Clean up `database.py`** — Remove unused `get_prediction_history`, `get_prediction_stats` functions
4. **Verify Analytics Dashboard** — Ensure `/api/analytics` endpoint works fully
5. **Test Full Flow** — Make prediction → verify schedule advisory updates → verify DB storage

---

## Quick Reference

**Default Admin**: `admin` / `admin123`
**Frontend URL**: `http://localhost:5173`
**Backend URL**: `http://localhost:8000`
**API Docs**: `http://localhost:8000/docs`
**GitHub Repo**: `https://github.com/springboardmentor443m-coder/Predictive-Public-Transit-Intelligence-Platform-for-Crowd-Management-and-Schedule-Optimization`
**Branch**: `anumitha-j`

---

*Generated for MetroFlow project documentation purposes.*
