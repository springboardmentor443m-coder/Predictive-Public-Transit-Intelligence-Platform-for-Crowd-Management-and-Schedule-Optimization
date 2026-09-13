# MetroFlow — AI Platform for Metro Crowd Management & Scheduling

MetroFlow is an AI-powered metro crowd management and scheduling platform that helps metro
authorities monitor passenger flow, predict crowd density, and optimize train scheduling in
real time. It integrates AI analytics, scheduling automation, crowd prediction, and operational
monitoring into one centralized application for smart transportation systems.

## Key Capabilities

| Module | Features |
|---|---|
| User Management | Admin/operator login, role-based access control (RBAC), profile management |
| Crowd Monitoring | Passenger density tracking (ticketing + sensor data), heatmaps, congestion monitoring, station-wise analytics, inflow/outflow analysis |
| Scheduling Management | Train schedule CRUD, peak-hour optimization, frequency adjustment, delay handling |
| AI Prediction | Crowd prediction models, passenger demand forecasting, traffic pattern analysis, smart recommendations |
| Alert & Notification | Overcrowding alerts, delay notifications, emergency announcements, real-time updates (Socket.IO) |
| Analytics Dashboard | Traffic analytics, station performance reports, operational monitoring, AI insight panels |

> No computer vision / CCTV processing is used — all models are trained on transportation and
> operational passenger datasets (smart-card ticketing, entry/exit records, footfall, ridership,
> GPS/status, occupancy, delay logs).

## Tech Stack

* **Backend:** Python 3.11+, FastAPI, SQLAlchemy 2, Pydantic v2, JWT auth, Socket.IO
* **Frontend:** Next.js 14 (React 18), Tailwind CSS, Recharts, lucide-react, socket.io-client
* **Databases:** PostgreSQL (core relational), MongoDB (raw ticketing/sensor events), Redis (live cache)
* **AI/Analytics:** scikit-learn, pandas, NumPy, joblib model store
* **DevOps:** Docker + Docker Compose (PostgreSQL/MongoDB/Redis/backend/frontend), AWS/Azure ready

## Repository Layout

```
MetroFlow/
├── backend/
│   ├── app/
│   │   ├── main.py               # FastAPI app + Socket.IO mount
│   │   ├── core/                 # config, security (JWT), database sessions
│   │   ├── models/               # SQLAlchemy models (users, stations, trains, schedules, alerts, ridership)
│   │   ├── schemas/              # Pydantic request/response schemas
│   │   ├── api/v1/               # REST endpoints per module
│   │   ├── services/             # business logic: crowd, scheduling, prediction, alerts, analytics, realtime
│   │   └── ml/                   # feature engineering + model wrappers
│   ├── scripts/
│   │   ├── generate_data.py      # synthetic transportation datasets (CSV) -> data/
│   │   ├── train_models.py       # trains crowd + demand models -> models_store/
│   │   └── seed_db.py            # seeds stations/trains/users/schedules/history
│   ├── data/                     # generated datasets (CSV)
│   ├── models_store/             # trained .joblib artifacts (legacy synthetic, {seoul,hangzhou}, nj delay)
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── pages/                    # login + professional dashboard suite
│   ├── components/               # layout, KPI cards, charts, heatmap, tables, modals
│   ├── lib/                      # API client, auth context, socket client
│   └── ...
├── docs/                         # PROJECT_PLAN + MILESTONE_1..4, DEPLOYMENT, PERFORMANCE_METRICS
├── deploy/k8s/metroflow.yaml     # Kubernetes manifests (all services)
├── postman/MetroFlow.postman_collection.json
├── backend/tests/test_api.py     # automated API test suite (pytest)
├── docker-compose.yml
└── README.md
```

## Quick Start (Local)

### 1. Infrastructure

Start the databases (PostgreSQL, MongoDB, Redis):

```bash
docker compose up -d postgres mongo redis
```

### 2. Backend

```bash
cd backend
python -m venv .venv
.\.venv\Scripts\activate                    # Windows
pip install -r requirements.txt
copy .env.example .env                      # adjust if needed

python scripts/generate_data.py             # create synthetic datasets in data/
python scripts/train_models.py              # train AI models
python scripts/seed_db.py                   # seed stations, trains, users, schedules

# Real-world (Kaggle-trained) models are served per city. Default is hangzhou.
set METROFLOW_MODEL_CITY=seoul              # or hangzhou (default)

uvicorn app.main:socket_app --reload --port 8000   # serves API + Socket.IO
```

API docs: http://localhost:8000/api/v1/docs

> macOS/Linux: use `source .venv/bin/activate` instead of `.\\.venv\\Scripts\\activate`,
> and `cp .env.example .env` instead of `copy`.

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Dashboard: http://localhost:3000

### Demo Accounts (created by seed script)

| Role | Email | Password |
|---|---|---|
| Admin | admin@metroflow.io | Admin@123 |
| Operator | operator@metroflow.io | Operator@123 |
| Viewer | viewer@metroflow.io | Viewer@123 |

## Docker (Full Stack)

```bash
docker compose up --build
```

Services: `frontend` (:3000), `backend` (:8000), `postgres` (:5432), `mongo` (:27017), `redis` (:6379).

## Operational Resilience (no Docker / partial services)

The backend runs and degrades gracefully even when an optional dependency is
down — end users never see raw stack traces (DB failures return a clean `503`):

| Dependency down  | Behavior |
|---|---|
| PostgreSQL       | DB-backed endpoints return `503 {"detail": "Database is temporarily unavailable..."}`; realtime loop backs off exponentially (5s → 120s) |
| Redis            | Auto-falls back to an in-memory cache, re-probes every 60s |
| MongoDB          | Sensor-event storage is skipped/disabled; no impact on APIs |
| No Docker at all | Use SQLite: `DATABASE_URL=sqlite:///./metroflow_dev.db`, then `python scripts/seed_db.py` |

`METROFLOW_ENABLE_REALTIME=0` disables the Socket.IO broadcast loop (used in tests/CI).

## Milestone Mapping (PRD)

* **Milestone 1 (Wk 1-2):** architecture, DB schema, auth + RBAC, crowd monitoring dashboard - [docs/MILESTONE_1.md](docs/MILESTONE_1.md)
* **Milestone 2 (Wk 3-4):** datasets, AI crowd/demand models, backend integration - [docs/MILESTONE_2.md](docs/MILESTONE_2.md)
* **Milestone 3 (Wk 5-6):** real-time monitoring, alerts, schedule optimization - [docs/MILESTONE_3.md](docs/MILESTONE_3.md)
* **Milestone 4 (Wk 7-8):** analytics, testing, Docker/cloud deployment, docs - [docs/MILESTONE_4.md](docs/MILESTONE_4.md)

See `docs/PROJECT_PLAN.md` for the full week-wise breakdown, `docs/PERFORMANCE_METRICS.md`
for measured model/API benchmarks, and `docs/DEPLOYMENT.md` for AWS/Azure/K8s deployment.

## Testing

```bash
cd backend
pip install -r requirements-dev.txt
pytest tests -v        # API suite (39 tests) + model wrapper suite (7 tests)
```

CI runs the same suite inside the built Docker image (Linux, pinned deps) plus
`npm run lint`/`npm run build` for the frontend (see `.github/workflows/ci.yml`).

## Contributing Guidelines

See [guidelines.md](guidelines.md) for the repository contributing guidelines for interns/collaborators.