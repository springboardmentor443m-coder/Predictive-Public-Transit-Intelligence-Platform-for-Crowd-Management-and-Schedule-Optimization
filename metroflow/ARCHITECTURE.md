# MetroFlow architecture

```
Browser dashboard (app/static/dashboard.html)  ->  FastAPI (app/main.py)
                                                        |
        +-----------------+-------------------+---------+---------+
        | core/security   | services/         | services/         | services/
        | JWT, roles      | crowd_monitoring  | ai_prediction     | scheduling
        |                 |                   |  (ML pipeline)    | alerts
        |                 |                   |                   | analytics
        +-----------------+---------+---------+-------------------+
                                      |
                        data/repository.py  (only CSV reader)
                                      |
        taipei_mrt_2yr.csv, station_capacity.csv, train_delays.csv
```

## Layers

- `main.py`: routes, input validation (date format and range, hour 0-23), role checks. No business logic.
- `core/security.py`: bcrypt password hashing, JWT (120 min), `admin` and `operator` roles. Operators are limited to their assigned station.
- `services/crowd_monitoring.py`: congestion % = entries / station capacity; bands Low <40, Moderate 40-70, High 70-90, Critical 90+.
- `services/ai_prediction.py`: training, evaluation, serving, anomaly detection. Artifacts are saved in `app/ml_artifacts/` (`demand_model.joblib`, `delay_model.joblib`, `model_metadata.json`) and cached in memory behind a lock.
- `services/scheduling.py`: forecast band to train interval (Low 10, Moderate 6, High 4, Critical 2.5 min); a delay of D minutes tightens the interval by 1 + D/15.
- `services/alerts.py`: overcrowding at 85% of capacity, delay at 7 min or more, anomalies beyond 3 sigma, emergency announcements.
- `services/analytics.py`: network traffic, station performance, operational summary, heatmap, AI insights.

## ML pipeline

1. Chronological split: development (83%) and test (17%).
2. Expanding-window cross-validation (6 blocks, 4 folds) ranks candidates: historical average, profile plus trend/seasonality, plus week-of-year, plus holiday calendar, direct gradient boosting.
3. The winner is evaluated once on the test period and then refit on all data for serving.
4. Intervals: Anscombe transform, residual quantiles from the 2 most recent folds, checked for coverage on test.
5. Anomalies: z-score of observed vs forecast on the same scale, flagged at |z| > 3.
6. Delay: HistGradientBoostingClassifier for P(delay) plus a regressor for severity, scored by ROC-AUC, PR-AUC and Brier score rather than accuracy.

## Testing

`tests/` holds 52 pytest tests: auth and roles, data integrity, crowd endpoints, ML quality gates (beats baseline, interval coverage, no leakage), scheduling, alerts and analytics. Fixtures train the models once per session.

## Deployment

`Dockerfile` (Python 3.12 slim, trains at build) and `docker-compose.yml`. Single process; for more load run several uvicorn workers or replicas, since the models are read-only after training.
