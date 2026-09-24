# MetroFlow — AI Platform for Metro Crowd Management & Scheduling

MetroFlow is an AI-powered metro crowd management and scheduling platform that helps metro
authorities monitor passenger flow, predict crowd density, and optimize train scheduling in
real time. It integrates AI analytics, scheduling automation, crowd prediction with **native
prediction intervals**, operational monitoring, and **real-world dataset ingestion** into one
centralized application for smart transportation systems.

The whole codebase is **TypeScript on the frontend** and a modern, deprecation-free Python
backend (`datetime.utcnow()` is banned in favour of the timezone-safe `app.core.time.utcnow()`).

## Key Capabilities

| Module | Features |
|---|---|
| User Management | Admin/operator login, role-based access control (RBAC), profile management |
| Crowd Monitoring | Passenger density tracking (ticketing + sensor data), heatmaps, congestion monitoring, station-wise analytics, inflow/outflow analysis |
| Train Monitoring | Live fleet position & status per train (in-transit / at-station / delayed...), position %, next stop, ETA, headway, projected load — streamed via Socket.IO with per-train rooms |
| Scheduling Management | Train schedule CRUD, peak-hour optimization, frequency adjustment, delay handling |
| AI Prediction | Crowd prediction & demand forecasting for any chosen date/time, **with lower/upper confidence intervals from an ensemble of quantile models**; per-train per-stop forecasts, traffic pattern analysis, smart recommendations |
| Alert & Notification | Overcrowding alerts, delay notifications, emergency announcements, real-time updates (Socket.IO) |
| Analytics Dashboard | Traffic analytics, station performance reports, operational monitoring, AI insight panels |
| Dataset Importers | Ingest genuine MTA / Seoul Metro / TfL CSVs into `data/` and feed the whole seed pipeline (`scripts/importers/`) |

> No computer vision / CCTV processing is used — all models are trained on transportation and
> operational passenger datasets (smart-card ticketing, entry/exit records, footfall, ridership,
> GPS/status, occupancy, delay logs).

## Tech Stack

* **Backend:** Python 3.11+, FastAPI, SQLAlchemy 2, Pydantic v2, JWT auth, Socket.IO
* **Frontend:** Next.js 14 (React 18) — **fully TypeScript**, Tailwind CSS, Recharts, lucide-react, socket.io-client
* **Databases:** PostgreSQL (core relational), MongoDB (raw ticketing/sensor events), Redis (live cache)
* **AI/Analytics:** scikit-learn (GradientBoosting, incl. **quantile regression**), pandas, NumPy, joblib model store
* **DevOps:** Docker + Docker Compose (PostgreSQL/MongoDB/Redis/backend/frontend), AWS/Azure ready

## Repository Layout

```
MetroFlow/
├── backend/
│   ├── app/
│   │   ├── main.py               # FastAPI app + Socket.IO mount + public GET /api/v1/health
│   │   ├── core/                 # config, security (JWT), database sessions, time helpers
│   │   ├── models/               # SQLAlchemy models (users, stations, trains, schedules, alerts, ridership)
│   │   ├── schemas/              # Pydantic request/response schemas (modern | None typing)
│   │   ├── api/v1/               # REST endpoints per module (incl. trains, predictions)
│   │   ├── services/             # business logic: crowd, scheduling, prediction, alerts, analytics, realtime, train_monitor
│   │   └── ml/                   # feature engineering + model wrappers (crowd/demand/delay, quantile intervals)
│   ├── scripts/
│   │   ├── generate_data.py      # synthetic transportation datasets (CSV) -> data/
│   │   ├── train_models.py       # trains legacy crowd + demand models -> models_store/
│   │   ├── train_quantile_crowd.py   # trains the advanced quantile crowd model (3 models: q05/q50/q95)
│   │   ├── seed_db.py            # seeds stations/trains/users/schedules/history (headway-driven) + --refresh
│   │   └── importers/            # MTA / Seoul / TfL real-dataset importers -> data/ (cli.py entrypoint)
│   ├── data/                     # generated or imported datasets (CSV)
│   ├── models_store/             # trained .joblib artifacts (legacy, {seoul,hangzhou}, nj delay, quantile crowd)
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── pages/                    # login + professional dashboard suite (TypeScript + Tailwind)
│   ├── components/               # layout, KPI cards, charts, heatmap, tables, modals
│   ├── lib/                      # API client, auth context, socket client
│   └── ...
├── docs/
│   ├── PROJECT_PLAN.md           # master plan + API surface
│   ├── MILESTONE_1..4.md         # weekly milestone reports
│   ├── DEPLOYMENT.md             # AWS / Azure / Kubernetes guides
│   ├── PERFORMANCE_METRICS.md    # model + API benchmarks
│   ├── IMPORTERS.md              # real-world dataset ingestion guide
│   ├── ML_MODELS.md              # model store, quantile intervals, training & fallbacks
│   └── ...
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
python scripts/train_models.py              # train legacy AI models (optional)
python scripts/train_quantile_crowd.py      # train the advanced quantile crowd model (optional, recommended)
python scripts/seed_db.py                   # seed stations, trains, users, schedules
python scripts/seed_db.py --refresh         # anytime: roll the demo forward (7-day schedule+ridership history & next-24h window; keeps user data)

# Real-world (Kaggle-trained) models are served per city. Default is hangzhou
# (best validation: crowd R² 0.896, demand R² 0.923).
set METROFLOW_MODEL_CITY=hangzhou           # or seoul | nyc | tfl | beijing

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

## Ingesting Real-World Datasets

MetroFlow ships first-class importers for genuine transit-agency CSVs. Each importer parses the
real export format, normalizes it to the demo's hourly schema (`ridership_hourly.csv` +
`stations.csv`), re-anchors it to *now* so the live dashboards stay fresh, and hands the result
straight to `seed_db.py`:

```bash
cd backend

# MTA turnstile (the weekly open-data turnstile_*.txt cumulative counters)
python scripts/importers/cli.py --city mta --input path/to/turnstile_240515.txt --output-dir data

# Seoul Metro card-swipe CSVs (English or Korean columns, hourly or daily totals)
python scripts/importers/cli.py --city seoul --input path/to/seoul_metro.csv --output-dir data

# TfL Entry & Exit annual counts
python scripts/importers/cli.py --city tfl --input path/to/tfl_entry_exit.csv --output-dir data

python scripts/seed_db.py --refresh   # load the imported data into the database
```

Station lines and fleet fallbacks are handled automatically on refresh. Full documentation of
formats, column aliases, the normalization pipeline, and how to add a new city live in
[`docs/IMPORTERS.md`](docs/IMPORTERS.md).

## ML Models & Confidence Intervals

`GET /predictions/crowd` (and `/predictions/demand`) returns `lower` / `upper` bounds for every
forecast point alongside the point prediction. With the advanced quantile artifact loaded
(`models_store/hangzhou_crowd_quantile_model.joblib`, trained by `train_quantile_crowd.py`), these
bounds come from an **ensemble of three GradientBoostingRegressors trained on quantile loss**
(α = 0.05 / 0.50 / 0.95) — a genuine uncertainty estimate. Legacy and synthetic artifacts fall
back to a symmetric residual-std band, so the API shape never changes.

- Model store, per-city selection (`METROFLOW_MODEL_CITY`), and training/fallback details:
  [`docs/ML_MODELS.md`](docs/ML_MODELS.md)
- Measured metrics (R² / MAE / coverage): [`docs/PERFORMANCE_METRICS.md`](docs/PERFORMANCE_METRICS.md)

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

A public `GET /api/v1/health` endpoint backs the login page and Kubernetes probes — it is
**unauthenticated** and reports reachability without leaking data. The login screen pings it to
decide "online / offline" instead of probing an auth-protected route (which previously caused a
false *"Backend Offline"*).

## Milestone Mapping (PRD)

* **Milestone 1 (Wk 1-2):** architecture, DB schema, auth + RBAC, crowd monitoring dashboard - [docs/MILESTONE_1.md](docs/MILESTONE_1.md)
* **Milestone 2 (Wk 3-4):** datasets, AI crowd/demand models, backend integration - [docs/MILESTONE_2.md](docs/MILESTONE_2.md)
* **Milestone 3 (Wk 5-6):** real-time monitoring, alerts, schedule optimization - [docs/MILESTONE_3.md](docs/MILESTONE_3.md)
* **Milestone 4 (Wk 7-8):** analytics, testing, Docker/cloud deployment, docs - [docs/MILESTONE_4.md](docs/MILESTONE_4.md)

Engineering hardening delivered after Milestone 4 (TypeScript conversion, quantile confidence
intervals, dataset importers, real-time traffic-curve fix, Python hygiene, login health check)
is tracked in the [`CHANGELOG.md`](CHANGELOG.md).

See `docs/PROJECT_PLAN.md` for the full week-wise breakdown, `docs/PERFORMANCE_METRICS.md`
for measured model/API benchmarks, and `docs/DEPLOYMENT.md` for AWS/Azure/K8s deployment.

## Testing

```bash
cd backend
pip install -r requirements-dev.txt
pytest tests -v        # API suite (52 tests) + model wrapper suite (7 tests) = 59 tests
```

CI runs the same suite inside the built Docker image (Linux, pinned deps) plus
`npm run lint`/`npm run build` for the frontend (see `.github/workflows/ci.yml`).

## Contributing Guidelines

See [guidelines.md](guidelines.md) for the repository contributing guidelines for interns/collaborators.