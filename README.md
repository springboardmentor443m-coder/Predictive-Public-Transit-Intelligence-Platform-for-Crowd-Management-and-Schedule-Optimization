# MetroFlow — Intelligent Metro Operations Platform

> **AI-Driven Real-Time Subway Demand Forecasting, Station Congestion Analysis, and Operational Advisory Platform**

MetroFlow is a full-stack, enterprise-grade metro operations intelligence platform engineered for urban transit dispatchers and station operations managers. Powered by **official New York City MTA transportation data** (302,000+ historical hourly observations across top station complexes) and **live MTA GTFS-Realtime telemetry**, MetroFlow fuses multi-model machine learning, topological station graph propagation, real-time alert dispatching, and decision-support advisories into a high-density, mission-critical operations console.

---

## 📌 Problem Statement & Motivation

Metropolitan subway networks process millions of daily passenger journeys. Unexpected demand surges, service delays, and platform overcrowding trigger station bottlenecks, severe downstream service ripple effects, and passenger safety hazards.

Standard transit operations rely heavily on static timetables and reactive incident reporting. **MetroFlow** transforms transit operations from reactive firefighting into proactive management by bridging historical ridership intelligence with live GTFS-Realtime vehicle feeds to:
1. **Predict next-hour station demand** using machine learning trained on multi-year ridership trends ($R^2 = 95.48\%$).
2. **Forecast platform crowd risk** before physical platform overcrowding occurs.
3. **Analyze network congestion propagation** across interconnected station transfer complexes.
4. **Evaluate live GTFS delay severity** and recommend dynamic headway adjustments to dispatchers in real time.

---

## 🚀 Key Platform Features

- **📊 Passenger Traffic Analytics**: Diurnal 24-hour demand curves, weekday vs. weekend distributions, peak hour multipliers, and volume rankings across 12 high-traffic MTA station complexes.
- **🚨 Early Warning Crowd Risk Engine**: Multi-threshold percentile classifier categorizing platform risk into `LOW`, `MODERATE`, `HIGH`, and `CRITICAL` with explainable trigger factors.
- **🕸️ Network Congestion Propagation**: 23-station complex graph topology modeling multi-hop queue spillover and transfer connection pressure.
- **⚡ GTFS-Realtime Live Telemetry**: Live ingestion of MTA vehicle positions (all 8 subway groups), trip updates, arrival/departure delays, and official service alerts with staleness detection.
- **⏱️ Dynamic Scheduling Advisories**: Real-time decision-support recommending headway frequency adjustments and capacity allocations without altering automated railway signaling.
- **🔔 Operational Alert Center**: Automated threshold- and ML-driven operational alerts with acknowledgement lifecycles, severity filtering, and WebSocket broadcasting.
- **🔒 Enterprise Security & RBAC**: OAuth2 JWT authentication, role-based access control (`ADMIN`, `OPERATOR`), password management, and an immutable security & operational audit trail.
- **🌓 Modern Operations UI**: Responsive operations matrix built with React 18, Vite, Lucide Icons, and Tailwind CSS with real-time WebSocket telemetry updates.

---

## 🏗️ System Architecture

```mermaid
graph TD
    subgraph Data Layer
        A[MTA SODA Historical Ridership API<br/>302k Records] -->|Data Pipeline| B[Engineered Feature Sets & Baseline Metrics]
        C[MTA GTFS-RT Live Feeds<br/>8 Subway Groups + Alerts] -->|Protobuf Streams| D[Live Data Ingestion Engine]
    end

    subgraph ML & Intelligence Layer
        B --> E[Demand Regressor<br/>RandomForest R² = 95.48%]
        B --> F[Crowd Risk Engine<br/>P50 / P80 / P95 Thresholds]
        B --> G[Network Congestion Model<br/>Accuracy = 96.85%]
        D --> H[Delay Severity Classifier<br/>Accuracy = 89.45%]
        E & F & G & H --> I[Dynamic Scheduling Advisories Engine]
    end

    subgraph Backend Core (FastAPI)
        E & F & G & H & I --> J[FastAPI REST API v1]
        D --> J
        J -->|JWT Auth & RBAC| K[(SQLite / PostgreSQL DB)]
        J -->|Stateful Logging| L[Audit Trail Engine]
        J -->|Events & Pings| M[Authenticated WebSocket Broadcaster]
    end

    subgraph Frontend Application (React + TypeScript)
        J -->|REST APIs| N[Executive Dashboard & Live Monitoring]
        M -->|Real-Time Push| N
        N --> O[ML Intelligence & Analytics Hub]
        N --> P[RBAC User & Audit Management]
    end
```

---

## 🛠️ Technology Stack

| Domain | Technologies |
| :--- | :--- |
| **Backend Framework** | Python 3.11+, FastAPI, Uvicorn, Pydantic v2 |
| **ORM & Database** | SQLAlchemy, SQLite (zero-config local dev), PostgreSQL (production/docker) |
| **Security & Auth** | OAuth2 Password Bearer, JWT (python-jose), Passlib (bcrypt hashing), RBAC |
| **Machine Learning & Data** | Scikit-Learn, Pandas, NumPy, Joblib, NetworkX |
| **Live Telemetry & Real-Time** | MTA GTFS-Realtime Protobuf, AsyncIO, WebSockets |
| **Frontend Framework** | React 18, TypeScript, Vite, Tailwind CSS, Lucide Icons |
| **Testing & Quality** | Pytest (48 backend tests), Vitest (frontend tests), TypeScript strict check |
| **DevOps & Containers** | Docker, Docker Compose |

---

## 🤖 Machine Learning Models & Performance

MetroFlow utilizes specialized models trained on chronological time-series splits:

| Model | Objective | Algorithm | Performance Metric | Primary Drivers |
| :--- | :--- | :--- | :--- | :--- |
| **Demand Forecasting** | Predict next-hour ridership | `RandomForestRegressor` | **$R^2 = 95.48\%$**, MAE = 258.73 pax, RMSE = 534.87 | `lag_168h` (Weekly Seasonality), `rolling_mean_24h`, `lag_24h` |
| **Crowd Risk Engine** | Classify platform risk tier | Multi-Threshold Percentile | $P_{50}, P_{80}, P_{95}$ Thresholds | Station-specific historical hourly distributions |
| **Network Congestion** | Multi-hop transfer spillover | `RandomForestClassifier` | **Accuracy = 96.85%** | Station graph adjacency, line interconnectivity |
| **Delay Severity** | Categorize delay ripple severity | `RandomForestClassifier` | **Accuracy = 89.45%**, Precision = 90.52%, F1 = 88.67% | Live arrival/departure delays, terminal bottlenecks |

---

## 📊 Dataset Description

MetroFlow is built on official public transit datasets from New York State:
- **MTA Subway Hourly Ridership (2020–2024)** (`wujg-7c2s`): 302,173 validated hourly records across 12 high-traffic NYC subway station complexes.
- **MTA Station Metadata** (`39hk-dx4f`): Geographic coordinates, line routes, complex structures, and ADA accessibility.
- **MTA GTFS-Realtime Feeds**: Live vehicle position streams and trip delay updates for lines `1-7`, `A/C/E`, `B/D/F/M`, `G`, `J/Z`, `L`, `N/Q/R/W`, and `SIR`.
- **MTA Service Alerts**: Live incident reports, service changes, and official delay bulletins.

### Target NYC Station Complexes
`Times Sq-42 St` (611), `Grand Central-42 St` (610), `34 St-Herald Sq` (607), `14 St-Union Sq` (602), `34 St-Penn Station (A,C,E)` (164), `Flushing-Main St` (447), `34 St-Penn Station (1,2,3)` (318), `Jackson Hts-Roosevelt Av` (616), `Fulton St` (628), `59 St-Columbus Circle` (614), `Chambers St/WTC` (624), `14 St/6 Av` (601).

---

## 🔒 Data State Integrity & Declarations

MetroFlow strictly categorizes all operational measurements into 4 distinct, truthful data states:
- **`LIVE`**: Verified GTFS-RT vehicle telemetry, live trip delays, feed health status, and active service alerts.
- **`HISTORICAL`**: Archived MTA SODA hourly turnstile ridership data and station metadata.
- **`PREDICTED`**: Machine learning model inferences (hourly demand forecasts, crowd risk tiers, graph congestion propagation).
- **`UNAVAILABLE`**: Exact physical train-car passenger load and station turnstile exit taps (neither is captured in public MTA feeds; explicitly declared `UNAVAILABLE` rather than simulated or guessed).

---

## 📁 Repository Structure

```
metroflow-hack/
├── backend/                       # FastAPI backend application
│   ├── app/
│   │   ├── api/v1/                # REST endpoints & WebSocket routers
│   │   │   ├── health.py          # System health check
│   │   │   ├── auth.py            # OAuth2 JWT login & logout
│   │   │   ├── profile.py         # Self-service profile & password change
│   │   │   ├── users.py           # Admin user management (RBAC)
│   │   │   ├── audit.py           # Security & operations audit log access
│   │   │   ├── live.py            # Real-time GTFS-RT ingestion endpoints
│   │   │   ├── ml.py              # ML demand, risk, and scheduling endpoints
│   │   │   ├── alerts.py          # Operational alerts lifecycle
│   │   │   ├── websocket.py       # Authenticated real-time WebSocket broadcast
│   │   │   └── router.py          # Master API router
│   │   ├── core/                  # Configuration, database setup, JWT security
│   │   ├── db/                    # DB base models and init_db seeder
│   │   ├── models/                # SQLAlchemy ORM models (User, Alert, Audit, Vehicle, etc.)
│   │   ├── schemas/               # Pydantic v2 request/response schemas
│   │   ├── services/              # Business logic (ML, GTFS-RT ingestion, alerts, audit)
│   │   └── main.py                # FastAPI application entrypoint
│   ├── tests/                     # Pytest automated test suite (48 tests)
│   ├── requirements.txt           # Python dependencies
│   ├── Dockerfile                 # Backend container configuration
│   └── .env                       # Local environment variables
│
├── frontend/                      # React 18 + TypeScript + Vite frontend
│   ├── src/
│   │   ├── components/            # UI components (Header, Sidebar, Cards, Charts, Layout)
│   │   ├── contexts/              # AuthContext and ThemeContext
│   │   ├── hooks/                 # Custom hooks (WebSocket, live polling)
│   │   ├── pages/
│   │   │   ├── DashboardOverviewPage.tsx # High-level operations overview & KPIs
│   │   │   ├── LiveMonitoringPage.tsx    # Live vehicle telemetry & delay tracker
│   │   │   ├── MLDashboardPage.tsx       # ML demand, risk, advisories & topology
│   │   │   ├── AuditLogsPage.tsx         # Security & operational audit trail
│   │   │   ├── UserManagementPage.tsx    # Admin RBAC user directory
│   │   │   ├── ProfilePage.tsx           # User profile & credential settings
│   │   │   ├── LoginPage.tsx             # JWT login interface
│   │   │   └── NotFoundPage.tsx          # 404 handler
│   │   ├── routes/                # ProtectedRoute and RoleRoute guards
│   │   ├── services/              # API clients (auth, live, ml, alerts, audit, users)
│   │   ├── types/                 # TypeScript interfaces and type definitions
│   │   ├── tests/                 # Vitest frontend tests
│   │   └── App.tsx                # Client-side router configuration
│   ├── package.json               # Node.js dependencies & scripts
│   └── Dockerfile                 # Frontend container configuration
│
├── data/                          # Datasets, topological definitions & ML artifacts
│   ├── raw/                       # Raw MTA source data
│   ├── processed/                 # Trained models (.pkl), master CSVs, metrics
│   ├── station_network.json       # 23-station topological graph adjacency
│   ├── data_dictionary.md         # Schema & field descriptions
│   ├── data_quality_report.md     # Validation & data hygiene report
│   └── data_sources.md            # NY State SODA API documentation
│
├── docs/                          # Comprehensive technical documentation
│   ├── ARCHITECTURE.md            # In-depth architectural blueprint
│   ├── METROFLOW_COMPLETE_PROJECT_GUIDE.md # Technical implementation guide
│   └── NETWORK_TOPOLOGY.md        # Station complex graph specification
│
├── scripts/                       # Data processing & model training pipelines
│   ├── build_dataset.py           # SODA extraction & feature engineering
│   ├── train_demand_model.py      # Random Forest demand regressor training
│   ├── crowd_risk.py              # Percentile-based risk threshold generator
│   ├── network_congestion.py      # Station network congestion classifier training
│   └── train_delay_model.py       # Delay impact severity classifier training
│
├── .env.example                   # Environment configuration template
├── docker-compose.yml             # Full-stack container orchestration
└── README.md                      # Single master repository documentation
```

---

## ⚙️ How to Run Locally

### Prerequisites
- **Python**: 3.11+ (Python 3.12 supported)
- **Node.js**: v18+ (with npm)

---

### 1. Backend Setup (FastAPI)

```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment
python -m venv venv

# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Initialize local SQLite database & seed default Admin account
python -m app.db.init_db

# Start FastAPI development server
uvicorn app.main:app --reload --port 8000
```

- **Backend API**: `http://localhost:8000`
- **Interactive OpenAPI Documentation (Swagger)**: `http://localhost:8000/docs`
- **Alternative ReDoc Documentation**: `http://localhost:8000/redoc`

---

### 2. Frontend Setup (React + Vite)

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start Vite development server
npm run dev
```

- **Frontend Application**: `http://localhost:5173`

---

### 🔐 Default Seed Credentials

During database initialization, an administrative account is automatically seeded:

| Field | Value |
| :--- | :--- |
| **Email** | `admin@metroflow.io` |
| **Password** | `AdminPassword123!` |
| **Role** | `ADMIN` (Full System Access) |

*(Operators can also be created via the Admin User Management panel at `/admin/users`)*.

---

## 🐳 Running with Docker Compose

To deploy the entire production-ready containerized stack (PostgreSQL + FastAPI + Vite Frontend):

```bash
# From the project root
docker-compose up --build
```

- **Frontend App**: `http://localhost:5173`
- **Backend REST API**: `http://localhost:8000`
- **Interactive Swagger Docs**: `http://localhost:8000/docs`
- **PostgreSQL Database**: `localhost:5432` (`metroflow_db`)

---

## 🧪 Testing & Verification

### Backend Test Suite (Pytest — 48/48 Passing)
The backend test suite validates authentication, RBAC authorization, live MTA parsing, ML services, audit logging, feed health, and WebSocket handshakes:

```bash
cd backend
python -m pytest tests -v
```

```
====================== 48 passed in ~103s ======================
```

### Frontend Test Suite (Vitest)
```bash
cd frontend
npm test -- --run
```

### TypeScript Static Type Check
```bash
cd frontend
npx tsc --noEmit
```

---

## 📡 Complete REST & WebSocket API Overview

### 1. Health & System
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/health` | Backend service health, DB connectivity, provider status | No |

### 2. Authentication & Profile
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/auth/login` | OAuth2 password login, returns JWT access token | No |
| `GET` | `/api/v1/auth/me` | Retrieve current authenticated user profile | Yes |
| `POST` | `/api/v1/auth/logout` | Discard session and record logout audit event | Yes |
| `GET` | `/api/v1/profile` | Retrieve active profile details | Yes |
| `PUT` | `/api/v1/profile` | Update profile information (name, email) | Yes |
| `POST` | `/api/v1/profile/change-password` | Securely change current user's password | Yes |

### 3. Admin User Management & Audit Trail
| Method | Endpoint | Description | Required Role |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/users` | List all users with pagination | `ADMIN` |
| `POST` | `/api/v1/users` | Create user with assigned role (`ADMIN`, `OPERATOR`) | `ADMIN` |
| `GET` | `/api/v1/users/{user_id}` | Retrieve specific user details | `ADMIN` |
| `PUT` | `/api/v1/users/{user_id}` | Update user name, email, or role | `ADMIN` |
| `DELETE` | `/api/v1/users/{user_id}` | Deactivate or remove user account | `ADMIN` |
| `GET` | `/api/v1/audit-logs` | Retrieve immutable system audit records | `ADMIN` |

### 4. Live MTA GTFS-RT Telemetry
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/live/health` | Live feed health, latency ms, staleness detection | Yes |
| `GET` | `/api/v1/live/vehicles` | Active subway train positions with route filtering | Yes |
| `GET` | `/api/v1/live/trips` | Real-time trip schedules, stop sequences, and delays | Yes |
| `GET` | `/api/v1/live/alerts` | Active official MTA Subway service alerts | Yes |
| `POST` | `/api/v1/live/sync` | Trigger an immediate live MTA feed ingestion cycle | Yes |

### 5. Machine Learning & Predictive Intelligence
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/ml/summary` | Demand model metrics ($R^2$, MAE, RMSE) and risk counts | Yes |
| `GET` | `/api/v1/ml/predictions` | Hourly demand predictions with station/risk filtering | Yes |
| `GET` | `/api/v1/ml/stations` | Current forecast and crowd risk status for all target stations | Yes |
| `GET` | `/api/v1/ml/risk-distribution`| Risk breakdown percentages across the network | Yes |
| `GET` | `/api/v1/ml/feature-importance`| Feature importance rankings from trained Random Forest | Yes |
| `GET` | `/api/v1/ml/network-summary` | Network topology connectivity metrics and model accuracy | Yes |
| `GET` | `/api/v1/ml/delay-impact` | Route-level delay impact severity estimates | Yes |
| `GET` | `/api/v1/ml/network-risk` | Connected station congestion pressure & factors | Yes |
| `GET` | `/api/v1/ml/station/{name}` | In-depth historical trend and forecast for single station | Yes |
| `GET` | `/api/v1/ml/station/{name}/connections` | Direct topological connections and transfer lines | Yes |
| `GET` | `/api/v1/ml/scheduling-intelligence` | Dynamic headway recommendations & schedule advisories | Yes |
| `GET` | `/api/v1/ml/analytics/traffic` | Diurnal demand curves, peak multipliers, system load | Yes |
| `GET` | `/api/v1/ml/anomalies` | Unusual ridership surges and delay anomalies | Yes |
| `GET` | `/api/v1/ml/crowd-prediction` | Real-time inference using trained model + live delay features | Yes |

### 6. Operational Alerts & Notifications
| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/alerts/active` | Active operational alerts filtered by severity/type | Yes |
| `GET` | `/api/v1/alerts/history` | Historical operational alert resolution log | Yes |
| `GET` | `/api/v1/alerts/summary` | Alert count breakdown for operations dashboard | Yes |
| `POST` | `/api/v1/alerts/{alert_id}/acknowledge` | Acknowledge alert with audit logging | Yes |

### 7. Real-Time Infrastructure (WebSockets)
| Protocol | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `WS` | `/api/v1/ws/events?token={jwt}` | Real-time live event broadcast stream | Yes (Query Token) |
| `POST` | `/api/v1/ws/test-event` | Development test event trigger (labeled DEV_TEST) | No |

---

## 🎯 Operational Limitations & Boundary Declarations

1. **Turnstile Exit Counts**: MTA ridership data tracks turnstile entry swipes/taps; exit taps are not captured in public MTA feeds and are explicitly declared `UNAVAILABLE`.
2. **Physical Car Occupancy**: Real-time train-car weight sensors and passenger counts are not provided in MTA GTFS-RT feeds; car passenger density is explicitly marked `UNAVAILABLE`.
3. **Train GPS Coordinates**: MTA GTFS-RT provides discrete stop sequences rather than high-frequency GPS coordinate breadcrumbs.
4. **Advisory Decision Support**: MetroFlow is an advisory decision-support platform for human transit dispatchers. It does **not** execute automated railway interlocking or physical signaling commands.

---

## 📄 License & Credits

Built with official public transit data provided by the **New York State Metropolitan Transportation Authority (MTA)** via `data.ny.gov` and MTA Real-Time Feeds.
