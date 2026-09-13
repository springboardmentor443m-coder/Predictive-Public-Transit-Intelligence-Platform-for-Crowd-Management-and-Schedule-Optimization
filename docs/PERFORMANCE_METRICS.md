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

### 1.1 Real-world Kaggle-trained models (Seoul / Hangzhou)

Trained with `kaggle/01_seoul_crowd_demand.py` and `kaggle/02_hangzhou_crowd_demand.py`
(XGBoost, held-out 20% split).

| Dataset | Model | R² | MAE | Peak-hour MAE |
|---|---|---|---|---|
| Seoul | Crowd | 0.472 | 0.102 (occupancy) | 0.148 |
| Seoul | Demand | 0.689 | 331 pax/hour | 483 |
| Hangzhou | Crowd | 0.896 | 0.053 (occupancy) | 0.102 |
| Hangzhou | Demand | 0.923 | 149 pax/hour | — |

Served by the API through `model_wrappers`: the `METROFLOW_MODEL_CITY` env var selects
`{city}_crowd_model.joblib` / `{city}_demand_model.joblib` from `models_store/` (default
`hangzhou`). The feature schema is read from each artifact's own metadata
(`stations`, `cap_norm_scale`), so inference builds the exact trained vector width
(Seoul 108, Hangzhou 88). Backend stations ST01–ST10 map to real station codes in
`app/ml/registry.py`. To refresh, rerun the Kaggle scripts (early stopping enabled,
`early_stopping_rounds=25`) and drop the zipped outputs into `models_store/`.

### 1.2 NJ Transit delay models (real-world)

Trained with `kaggle/03_nj_transit_delay.py` (XGBoost, 3M stop-level rows from
2018-03 .. 2020-05, held-out 20%).

| Model | Metric | Value |
|---|---|---|
| Delay classifier (on_time / minor_delay / delayed) | accuracy | 0.535 |
| | macro ROC-AUC | 0.733 (on_time 0.76, minor 0.69, delayed 0.75) |
| | delayed class F1 | 0.45 |
| Delay regressor (minutes) | R² | 0.216 |
| | MAE | 3.15 min |
| | delayed-only MAE | 7.43 min |

Served via `POST /api/v1/predictions/delay`. Inputs are the model's real feature
space (line, from/to station, stop sequence, scheduled time, weekday, train type);
top features are `line` (Princeton Shuttle, Atl. City Line, Northeast Corridor),
schedule phase (`sched_sin`) and weekend flag. There is no synthetic fallback —
the endpoint returns 503 only if artifacts are missing. Refreshing does not require
retraining: the current model already reflects the dataset ceiling for a
line/schedule level delay target.

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
