# MetroFlow — ML Models & Confidence Intervals

Everything about the machine-learning layer: the model store, per-city selection, the advanced
**quantile-ensemble crowd model** that powers native prediction intervals, how the API consumes
them, and the graceful fallbacks when artifacts are missing.

## 1. Model Store (`backend/models_store/`)

Artifacts are `joblib` bundles. Each bundle is a dict carrying the estimator plus its encoding
metadata (`stations`, `feature_names`, `cap_norm_scale`, `residual_std`, `trained_on`) so
inference reproduces the exact trained feature schema.

| Artifact | Model | Serves |
|---|---|---|
| `crowd_model.joblib` | GradientBoostingRegressor (synthetic) | legacy crowd fallback |
| `demand_model.joblib` | GradientBoostingRegressor (synthetic) | legacy demand fallback |
| `{seoul,hangzhou}_crowd_model.joblib` | XGBoost (Kaggle) | per-city crowd |
| `{seoul,hangzhou}_demand_model.joblib` | XGBoost (Kaggle) | per-city demand |
| `hangzhou_crowd_quantile_model.joblib` | **3 × GradientBoostingRegressor (quantile loss: α = 0.05, 0.50, 0.95)** | advanced crowd with native lower/upper intervals |
| `delay_classifier.joblib` + `delay_regressor.joblib` | XGBoost (NJ Transit NEC) | per-train delay inference (`POST /predictions/delay`) |

City selection is controlled by `METROFLOW_MODEL_CITY` (`seoul | hangzhou | nyc | tfl | beijing`,
default `hangzhou`); the station mapping (ST01–ST10 → real city codes) lives in
`app/ml/registry.py`.

## 2. The Advanced Crowd Model (quantile ensemble)

`scripts/train_quantile_crowd.py` trains **three independent GradientBoostingRegressors with
quantile loss** on the same feature schema used at inference:

- α = 0.05 → pessimistic ("lower") forecast
- α = 0.50 → median ("center", the point prediction)
- α = 0.95 → optimistic ("upper") forecast

When the API loads a crowd artifact whose metadata carries `kind: "quantile"`, `CrowdModel`
treats the three estimators as a genuine uncertainty model: every forecast point returns
`lower ≤ center ≤ upper` sourced from the trained quantiles instead of a fixed symmetric band.

```bash
cd backend
python scripts/train_quantile_crowd.py                      # defaults: data/ridership_hourly.csv → models_store/hangzhou_crowd_quantile_model.joblib
python scripts/train_quantile_crowd.py --estimators 300 --depth 6 --out models_store/x.joblib
```

Measured on the held-out 20% split (synthetic dataset, 10 stations):

| Metric | Value |
|---|---|
| MAE | 0.0282 (occupancy units) |
| R² | 0.9803 |
| residual_std | 0.0406 |

### Feature schema

The trainer and the runtime wrapper both use `features.kaggle_row_features()`:

```
[7 temporal] hour/weekday cyclic encodings + is_peak + is_weekend + weekend_peak
[ N station one-hot ] over the artifact's Hangzhou codes (10)
[1 capacity_norm]    capacity / cap_norm_scale (700), clipped to [0, 1.5]
```

Backend stations ST01–ST10 map to Hangzhou codes via `registry.CITY_STATION_MAP["hangzhou"]`
(e.g. ST01 → `"015"`). Because one-hot order is stored in the artifact, the same wrapper loads
any city's crowd/demand model unchanged.

## 3. How the API returns intervals

`predict_hourly` (`GET /predictions/crowd?hours=...`) and `predict_period`
(`?start_time=...&hours=...`) resolve three arrays — center / lower / upper — via
`CrowdModel._predict_bounds()`:

- **Quantile artifact loaded** → `lower = q05 predictions`, `center = q50`, `upper = q95`
  (clamped to `[0.05, 1.2]` before conversion to percent, then `[0, 100]`).
- **Legacy/synthetic artifact** → fallback symmetric band `center ± residual_std`.
- **No artifact** → rule-based baseline curve, also with a residual band.

Response shape is identical in all cases:

```json
{
  "hour": 8,
  "predicted_occupancy_pct": 92.92,
  "lower": 80.89,
  "upper": 99.86,
  "congestion_level": "critical",
  "timestamp": "2026-09-24T19:12:28Z"
}
```

`DemandForecaster` mirrors the confidence-band behaviour for the demand endpoint.

The frontend renders the interval as an uncertainty band on crowd/demand charts
(`dashboard/predictions.tsx`); the interval width is a live indicator of model confidence.

## 4. Graceful Degradation

| Artifact missing | Crowd/demand | Delay |
|---|---|---|
| None | rule-based baseline (no crash, `logger.warning`) | clean `503`, never `500` |
| City artifact absent, legacy present | legacy fallback via `_city_file()` | — |
| Quantile artifact absent | symmetric residual band | — |
| joblib not installed | rule-based baseline | `503` |

## 5. Retraining & Promotion

1. Kaggle city models: run `kaggle/01..06_*.py`; copy `{city}_model_outputs/{crowd,demand}_model.joblib`
   into `models_store/` as `{city}_crowd/demand_model.joblib`.
2. Advanced (quantile) crowd model: `python scripts/train_quantile_crowd.py`.
3. Synthetic baseline: `python scripts/train_models.py`.
4. NJ delay: `kaggle/03_nj_transit_delay.py` → `delay_classifier.joblib` / `delay_regressor.joblib`.

Live provenance for every loaded artifact (city, algorithm, R², dataset, timestamp) is exposed at
`GET /api/v1/predictions/model-info` and rendered as the ModelBadge on the AI Predictions page.

Full accuracy tables for all models are in [`docs/PERFORMANCE_METRICS.md`](PERFORMANCE_METRICS.md).