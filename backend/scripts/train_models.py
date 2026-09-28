"""Train the NYC crowd + demand artifacts on the repo's real MTA ridership data.

The previous artifacts (`crowd_model.joblib` / `demand_model.joblib`) were
trained against the invented 10-station world: their `stations` list held
`ST01..ST10` and their estimators expected 18 features. `features.py` now
encodes the 51 real MTA stop ids (59 features), so those estimators raised on
every `predict()` call, the exception was swallowed, and `/predictions/crowd`
silently served the rule-based baseline while `/model-info` still advertised a
trained model. This script produces artifacts whose encoding matches inference
exactly.

Two deliberate choices:

* The features are built with `kaggle_row_features`, the same builder the
  inference path takes when an artifact declares `trained_on` in `_KAGGLE_CITIES`.
  Training and serving have to agree column-for-column, so both go through the
  artifact's own `stations` list and `cap_norm_scale`.
* The split is chronological, not random. A random split puts the same station
  and hour on both sides of the boundary, which leaks and inflates R²; a model
  that has only ever been scored that way is not calibrated for forecasting.

Usage:
    .\\.venv\\Scripts\\python.exe scripts/train_models.py
"""

import argparse
import json
import os
import sys

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, r2_score

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ml import features as feat  # noqa: E402

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models_store")

CITY = "nyc"
HOLDOUT_DAYS = 7
RANDOM_STATE = 42


def build_features(df: pd.DataFrame) -> np.ndarray:
    """Encode rows exactly the way inference will.

    Mirrors `CrowdModel._feature_rows` / `DemandForecaster._feature_rows` for a
    kaggle-style artifact: temporal block, one-hot over the artifact's station
    list, then normalised capacity.
    """
    codes = [str(c) for c in df["station_code"]]
    hours = df["hour"].to_numpy(dtype=int)
    weekdays = df["weekday"].to_numpy(dtype=int)
    caps = df["capacity"].to_numpy(dtype=float)
    return np.array([
        feat.kaggle_row_features(int(h), int(w), code, float(cap), feat.STATION_LIST, feat.MAX_CAPACITY)
        for h, w, code, cap in zip(hours, weekdays, codes, caps)
    ])


def _chronological_split(df: pd.DataFrame, holdout_days: int):
    """Split on the timestamp, holding out the most recent `holdout_days`.

    The last fortnight of the window becomes the validation set so the reported
    score reflects forecasting unseen hours rather than interpolating them.
    """
    cutoff = df["timestamp"].max().normalize() - pd.Timedelta(days=holdout_days)
    train = df[df["timestamp"] < cutoff]
    test = df[df["timestamp"] >= cutoff]
    return train, test, cutoff


def _fit(name: str, X_train, y_train, X_test, y_test):
    model = GradientBoostingRegressor(
        n_estimators=300, max_depth=4, learning_rate=0.08, subsample=0.9,
        random_state=RANDOM_STATE,
    )
    model.fit(X_train, y_train)
    preds = model.predict(X_test)
    mae = float(mean_absolute_error(y_test, preds))
    r2 = float(r2_score(y_test, preds))
    residual_std = float(np.std(np.asarray(y_test) - preds))
    print(f"[{name}]  MAE={mae:.4f}  R2={r2:.4f}  residual_std={residual_std:.4f}")
    return {
        "model": model,
        "residual_std": residual_std,
        "stations": list(feat.STATION_LIST),
        "cap_norm_scale": float(feat.MAX_CAPACITY),
        "trained_on": CITY,
        "feature_names": feature_names(),
        "n_rows": int(len(X_train) + len(X_test)),
        "metrics": {"r2": r2, "mae": mae},
    }


def feature_names() -> list[str]:
    return (
        ["hour_sin", "hour_cos", "is_peak", "is_weekend", "dow_sin", "dow_cos", "weekend_peak"]
        + [f"station_{c}" for c in feat.STATION_LIST]
        + ["capacity_norm"]
    )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--holdout-days", type=int, default=HOLDOUT_DAYS,
                    help="most recent N days reserved for validation (default: 7)")
    args = ap.parse_args()

    os.makedirs(MODELS_DIR, exist_ok=True)
    path = os.path.join(DATA_DIR, "ridership_hourly.csv")
    if not os.path.exists(path):
        sys.exit(f"{path} missing. Run scripts/generate_data.py first.")

    ridership = pd.read_csv(path, dtype={"station_code": str}, parse_dates=["timestamp"])
    unknown = sorted(set(ridership["station_code"].astype(str)) - set(feat.STATION_LIST))
    if unknown:
        sys.exit(
            f"Dataset has {len(unknown)} station code(s) absent from features.STATION_LIST: "
            f"{unknown}. Regenerate the data or update STATION_LIST — training on a code the "
            f"encoder cannot index would silently produce an all-zero one-hot row."
        )
    print(f"Loaded {len(ridership)} ridership records across {ridership['station_code'].nunique()} stations")

    # Crowd: platform load as a fraction of the station's hourly throughput,
    # matching the scale `predict_period` multiplies by 100.
    crowd = ridership.copy()
    crowd["target"] = (crowd["occupancy"] / crowd["capacity"]).clip(0.0, 1.2)

    # Demand: raw gate entries.
    demand = ridership.copy()
    demand["target"] = demand["entries"].astype(float)

    artifacts = {}
    for name, frame in (("crowd", crowd), ("demand", demand)):
        train_df, test_df, cutoff = _chronological_split(frame, args.holdout_days)
        print(f"[{name}]  train={len(train_df)} (before {cutoff:%Y-%m-%d})  holdout={len(test_df)}")
        X_train, X_test = build_features(train_df), build_features(test_df)
        artifacts[name] = _fit(
            name, X_train, frame.loc[train_df.index, "target"].to_numpy(),
            X_test, frame.loc[test_df.index, "target"].to_numpy(),
        )

    for name, artifact in artifacts.items():
        out = os.path.join(MODELS_DIR, f"{CITY}_{name}_model.joblib")
        joblib.dump(artifact, out)
        print(f"Saved {os.path.basename(out)}  ({os.path.getsize(out) / 1e6:.1f} MB)")

    metrics = {
        "city": CITY,
        "holdout_days": args.holdout_days,
        "stations": len(feat.STATION_LIST),
        "cap_norm_scale": float(feat.MAX_CAPACITY),
        "n_features": len(feature_names()),
        "crowd": artifacts["crowd"]["metrics"],
        "demand": artifacts["demand"]["metrics"],
    }
    metrics_path = os.path.join(MODELS_DIR, f"{CITY}_train_metrics.json")
    with open(metrics_path, "w", encoding="utf-8") as fh:
        json.dump(metrics, fh, indent=2)
    print(f"Saved {os.path.basename(metrics_path)}")
    print(f"Crowd R2: {metrics['crowd']['r2']:.4f} | Demand R2: {metrics['demand']['r2']:.4f}")


if __name__ == "__main__":
    main()
