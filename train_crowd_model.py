"""
Train the MetroFlow platform-crowd model
=======================================
The shipped model (metroflow_xgboost_model.json) predicts passengers *on board*
(Train_Occupancy_Count). The live dashboard, however, needs to compare the
*platform crowd* against a forecast of the *platform crowd* - comparing one
against the other would be meaningless.

This script trains a second regressor on Platform_Crowd_Density using exactly
the same nine features, evaluates it on a chronological hold-out, and writes
metroflow_crowd_model.json plus a metrics sidecar used by /api/ml/metrics.

Run:  python train_crowd_model.py
"""

from __future__ import annotations

import json
import os

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET = os.path.join(BASE_DIR, "AI_MetroFlow_Master_Dataset.xlsx")
OUT_MODEL = os.path.join(BASE_DIR, "metroflow_crowd_model.json")
OUT_META = os.path.join(BASE_DIR, "metroflow_crowd_metrics.json")

STATIONS = ["Botanical Garden", "Dwarka Sec 21", "Hauz Khas", "Kashmere Gate", "Rajiv Chowk"]
LINES = ["Blue Line", "Magenta Line", "Red Line", "Yellow Line"]
STATION_INDEX = {s: i for i, s in enumerate(STATIONS)}
LINE_INDEX = {ln: i for i, ln in enumerate(LINES)}

FEATURES = [
    "Entry_Hour", "Day_of_Week", "Is_Peak_Hour", "Hour_Sin",
    "Hour_Cos", "From_Station", "To_Station", "Line_Color", "Train_Capacity",
]

TARGET = "Platform_Crowd_Density"


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    ts = pd.to_datetime(df["Exact_Entry_Timestamp"])
    hour = ts.dt.hour
    peak = ((hour >= 8) & (hour <= 11)) | ((hour >= 17) & (hour <= 20))
    return pd.DataFrame({
        "Entry_Hour": hour,
        "Day_of_Week": ts.dt.dayofweek,
        "Is_Peak_Hour": peak.astype(int),
        "Hour_Sin": np.sin(2 * np.pi * hour / 24.0),
        "Hour_Cos": np.cos(2 * np.pi * hour / 24.0),
        "From_Station": df["From_Station"].map(STATION_INDEX),
        "To_Station": df["To_Station"].map(STATION_INDEX),
        "Line_Color": df["Line_Color"].map(LINE_INDEX),
        "Train_Capacity": df["Train_Capacity"],
    })


def main() -> None:
    df = pd.read_excel(DATASET)
    X = build_features(df)
    y = df[TARGET].astype(float)

    # chronological split - never shuffle, this is time-series data
    split = int(len(X) * 0.8)
    X_tr, X_te = X.iloc[:split], X.iloc[split:]
    y_tr, y_te = y.iloc[:split], y.iloc[split:]

    model = xgb.XGBRegressor(
        n_estimators=350,
        max_depth=6,
        learning_rate=0.08,
        subsample=0.9,
        colsample_bytree=0.9,
        min_child_weight=3,
        reg_lambda=1.0,
        random_state=42,
        tree_method="hist",
    )
    model.fit(X_tr, y_tr)

    pred = np.clip(model.predict(X_te), 0, None)
    resid = y_te.values - pred

    metrics = {
        "target": TARGET,
        "rows_total": int(len(X)),
        "rows_train": int(len(X_tr)),
        "rows_test": int(len(X_te)),
        "split_strategy": "Chronological 80/20 (no shuffling - respects time order)",
        "r2": round(float(r2_score(y_te, pred)), 4),
        "mae": round(float(mean_absolute_error(y_te, pred)), 2),
        "rmse": round(float(np.sqrt(mean_squared_error(y_te, pred))), 2),
        "mape": round(float(np.mean(np.abs(resid) / np.maximum(y_te.values, 1)) * 100), 2),
        "bias": round(float(np.mean(resid)), 2),
        "within_10pct": round(
            float(np.mean(np.abs(resid) / np.maximum(y_te.values, 1) < 0.10) * 100), 1),
    }

    model.save_model(OUT_MODEL)
    with open(OUT_META, "w", encoding="utf-8") as fh:
        json.dump(metrics, fh, indent=2)

    print("Platform-crowd model trained")
    print(json.dumps(metrics, indent=2))
    print("\nfeature importance:")
    for f, v in sorted(zip(FEATURES, model.feature_importances_),
                       key=lambda x: -x[1]):
        print("  %-16s %.4f" % (f, v))
    print("\nwrote %s" % OUT_MODEL)
    print("wrote %s" % OUT_META)


if __name__ == "__main__":
    main()