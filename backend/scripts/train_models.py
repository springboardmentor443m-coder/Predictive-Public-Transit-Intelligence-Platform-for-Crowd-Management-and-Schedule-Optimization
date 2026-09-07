import os
import sys

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ml.features import STATION_LIST, row_features  # noqa: E402

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models_store")


def build_features(df: pd.DataFrame) -> np.ndarray:
    rows = [
        row_features(int(h), int(d), str(sid))
        for h, d, sid in zip(df["hour"], df["weekday"], df["station_code"])
    ]
    return np.array(rows)


def train_crowd_model(ridership: pd.DataFrame):
    df = ridership.copy()
    X = build_features(df)
    y = (df["occupancy"].values / df["capacity"].values).astype(float)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = GradientBoostingRegressor(n_estimators=300, max_depth=4, learning_rate=0.08, subsample=0.9, random_state=42)
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    mae = mean_absolute_error(y_test, preds)
    r2 = r2_score(y_test, preds)
    residual_std = float(np.std(y_test - preds))
    print(f"[crowd]    MAE={mae:.4f}  R2={r2:.4f}  residual_std={residual_std:.4f}")
    return {"model": model, "residual_std": residual_std}, r2


def train_demand_model(ridership: pd.DataFrame):
    # Per-station hourly profile (NOT pooled means) so forecasts differ per station.
    df = ridership.groupby(["station_code", "hour", "weekday"], as_index=False)["entries"].mean()
    X = build_features(df)
    y = df["entries"].values.astype(float)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = GradientBoostingRegressor(n_estimators=300, max_depth=4, learning_rate=0.08, subsample=0.9, random_state=42)
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    mae = mean_absolute_error(y_test, preds)
    r2 = r2_score(y_test, preds)
    print(f"[demand]   MAE={mae:.1f}  R2={r2:.4f}")
    return {"model": model, "residual_std": float(np.std(y_test - preds))}, r2


def main() -> None:
    os.makedirs(MODELS_DIR, exist_ok=True)
    path = os.path.join(DATA_DIR, "ridership_hourly.csv")
    if not os.path.exists(path):
        print("Dataset missing. Run scripts/generate_data.py first.")
        sys.exit(1)

    ridership = pd.read_csv(path, parse_dates=["timestamp"])
    print(f"Loaded {len(ridership)} ridership records")

    crowd_artifact, crowd_r2 = train_crowd_model(ridership)
    demand_artifact, demand_r2 = train_demand_model(ridership)

    joblib.dump({**crowd_artifact, "stations": STATION_LIST}, os.path.join(MODELS_DIR, "crowd_model.joblib"))
    joblib.dump({**demand_artifact, "stations": STATION_LIST}, os.path.join(MODELS_DIR, "demand_model.joblib"))
    print(f"Saved models -> {MODELS_DIR}")
    print(f"Crowd R2: {crowd_r2:.4f} | Demand R2: {demand_r2:.4f}")


if __name__ == "__main__":
    main()
