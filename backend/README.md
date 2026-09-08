# 🚇 MetroFlow — Backend & Database Layer

This directory contains the entire backend services, database layer, REST API endpoints, machine learning inference pipeline, and automated test suite for the **MetroFlow AI Platform for Metro Crowd Management and Scheduling**.

---

## 🛠️ Technology Stack & Architecture

- **Runtime**: Python 3.11+ (Asynchronous ASGI)
- **Web Framework**: FastAPI 0.110+ (OpenAPI 3.0, Swagger UI, Pydantic v2)
- **ORM & Database**: SQLAlchemy 2.0 + PostgreSQL 16 (with SQLite zero-setup fallback)
- **Database Migrations**: Alembic 1.13
- **In-Memory Cache**: Redis 7 (5-minute TTL compound key caching)
- **Machine Learning**: Scikit-Learn 1.4+ (Random Forest Regressor) & LightGBM 4.3+
- **Security**: OAuth2 Bearer Tokens + JWT (HS256) + Bcrypt (`passlib`)

---

## 🗂️ Backend Directory Structure

```text
backend/
├── Dockerfile                   # Python 3.11-slim container definition
├── requirements.txt             # Python backend dependencies
├── alembic.ini                  # Alembic migration configuration
├── README.md                    # Backend documentation
├── alembic/                     # Database migrations
│   ├── env.py
│   └── versions/
│       └── 0001_initial_schema.py
├── app/
│   ├── main.py                  # FastAPI application entrypoint & lifespan
│   ├── core/                    # Settings, security & dependencies
│   │   ├── config.py
│   │   ├── dependencies.py
│   │   └── security.py
│   ├── db/                      # Session factory & database seed script
│   │   ├── base.py
│   │   ├── session.py
│   │   └── seed.py              # Seeds 131+ stations, 44k ridership curves
│   ├── models/                  # SQLAlchemy ORM models
│   │   ├── station.py
│   │   ├── ridership.py
│   │   ├── train_status.py
│   │   ├── alert.py
│   │   └── user.py
│   ├── schemas/                 # Pydantic v2 validation models
│   │   ├── auth.py
│   │   ├── station.py
│   │   ├── predict.py
│   │   ├── schedule.py
│   │   └── alert.py
│   ├── routers/                 # REST API endpoints
│   │   ├── auth.py              # /api/v1/auth
│   │   ├── stations.py          # /api/v1/stations
│   │   ├── predict.py           # /api/v1/predict
│   │   ├── schedule.py          # /api/v1/schedule
│   │   ├── alerts.py            # /api/v1/alerts
│   │   └── analytics.py         # /api/v1/analytics
│   ├── services/                # Business logic, scheduling & alert engines
│   │   ├── ml_loader.py
│   │   ├── scheduling.py
│   │   ├── scheduler.py
│   │   ├── alert_engine.py
│   │   └── cache.py
│   └── ml/                      # ML inference pipeline & fallback
│       └── model_loader.py
└── tests/                       # Automated backend test suite
    ├── test_api.py
    ├── test_scheduling.py
    └── test_alerts_engine.py
```

---

## 🚀 Quickstart: Local Setup & Execution

### 1. Environment & Dependencies

```bash
# Create and activate virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install required packages
pip install -r requirements.txt
```

### 2. Database Setup & Migrations

```bash
# Apply schema migrations to create all 5 tables
alembic upgrade head

# Seed database with 131+ stations, 44,000+ historical curves, trains, and alerts
python -m app.db.seed
```

### 3. Start Development Server

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

- **Swagger UI Docs**: [http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs)
- **ReDoc Schema**: [http://localhost:8000/api/v1/redoc](http://localhost:8000/api/v1/redoc)
- **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

---

## 🧪 Running Automated Tests

Execute the full automated test suite covering authentication, API routes, headway scheduling optimization, delay propagation, and the 15-minute alert engine:

```bash
pytest tests/ -v
```

---

## 🔑 Default Credentials

| Role | Username | Password | Access Level |
| :--- | :--- | :--- | :--- |
| **Station Manager** | `admin` | `admin123` | Full admin rights, schedule override, broadcast alerts |
| **Transit Operator** | `operator` | `operator123` | Real-time monitoring, alert acknowledgment |
