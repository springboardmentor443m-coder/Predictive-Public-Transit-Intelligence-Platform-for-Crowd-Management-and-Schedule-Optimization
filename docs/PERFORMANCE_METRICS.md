# MetroFlow — Performance Metrics

Measured on the development machine (Windows, Python 3.12, SQLite dev DB,
scikit-learn GradientBoosting). Regenerate model metrics with
`python scripts/train_models.py`; API timings via Postman or `curl -w "%{time_total}"`.

## 1. AI Model Accuracy (held-out test split)

| Model | Algorithm | R² | MAE | Artifact |
|---|---|---|---|---|
| Crowd density | GradientBoostingRegressor | **0.983** | 0.0068 (occupancy units) | `models_store/crowd_model.joblib` |
| Demand forecast | GradientBoostingRegressor | **0.993** | 2.4 passengers/hour | `models_store/demand_model.joblib` |

Both models are station-aware: features include one-hot station identity + normalized
capacity (encoding stored inside the artifact), so forecasts differ per station.
Unknown station IDs fall back to population-average behaviour.

Interpretation: crowd model explains ~98% of occupancy variance; demand model tracks
hourly entries closely on synthetic data (expected — strong generated signal).
Both degrade gracefully to heuristic baselines if artifacts are missing.

## 2. API Latency (local, warm)

| Endpoint | Typical response |
|---|---|
| `GET /api/v1/health` | < 10 ms |
| `POST /api/v1/auth/login` | ~2.5 s (pbkdf2 hashing; first request) |
| `GET /api/v1/crowd/live` | ~50 ms |
| `GET /api/v1/crowd/heatmap` | ~60 ms (10 stations × 24 h = 240 cells) |
| `GET /api/v1/predictions/crowd?hours=12` | ~80 ms (12 model inferences) |
| `GET /api/v1/predictions/patterns` | ~120 ms (7-day aggregation) |
| `POST /api/v1/scheduling/apply-headway/{id}` | ~70 ms |
| `GET /api/v1/analytics/overview` | ~40 ms |

## 3. Real-Time Layer

| Metric | Value |
|---|---|
| Broadcast interval | 5 s (`crowd_update`) |
| Snapshot payload | 10 stations × {occupancy_pct, congestion_level, inflow, outflow} |
| Alert dedup window | 15 min per (station, type) |
| Alert push latency | same cycle as detection (≤ 5 s) |
| Redis snapshot TTL | 30 s |

## 4. Data Volumes Handled

| Dataset | Size |
|---|---|
| Ridership records | 14,400 rows (10 stations × 24 h × 60 days) |
| Ticketing events (Mongo) | 20,000 generated / 5,000 seeded per run |
| Schedules | ~170 active timetable entries |
| Heatmap grid | 240 points per render |

## 5. Scalability Notes

- Backend is stateless → scale horizontally (k8s replicas=2 baseline).
- Socket.IO requires sticky sessions behind a load balancer.
- Redis + MongoDB have 60 s retry cooldowns; system runs fully without them
  (in-memory cache, SQL-only persistence), so partial cloud outages degrade
  gracefully instead of failing requests.
