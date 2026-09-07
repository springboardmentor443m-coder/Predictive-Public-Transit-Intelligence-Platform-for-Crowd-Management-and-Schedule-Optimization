import os
import joblib
import numpy as np
import pandas as pd
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score

from app.ml.data_generator import generate_synthetic_transit_dataset

SAVED_MODELS_DIR = os.path.join(os.path.dirname(__file__), "saved_models")
PROCESSED_DATASET = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "datasets", "processed", "master_transit_dataset.csv")
)
os.makedirs(SAVED_MODELS_DIR, exist_ok=True)


def train_demand_forecasting_models():
    if os.path.exists(PROCESSED_DATASET):
        print(f"Loading real-world master dataset from {PROCESSED_DATASET}...")
        df = pd.read_csv(PROCESSED_DATASET)
    else:
        print("Generating synthetic dataset for Demand Model training...")
        df = generate_synthetic_transit_dataset(days=14)

    # Feature engineering
    feature_cols = [
        "station_id",
        "hour",
        "minute",
        "day_of_week",
        "is_weekend",
        "capacity",
        "inflow_ppm",
        "outflow_ppm",
        "line_delay_min",
        "density_pct",
    ]

    X = df[feature_cols]
    y_15 = df["target_inflow_15m"]
    y_30 = df["target_inflow_30m"]
    y_60 = df["target_inflow_60m"]

    X_train, X_test, y15_train, y15_test = train_test_split(X, y_15, test_size=0.2, random_state=42)
    _, _, y30_train, y30_test = train_test_split(X, y_30, test_size=0.2, random_state=42)
    _, _, y60_train, y60_test = train_test_split(X, y_60, test_size=0.2, random_state=42)

    print("Training XGBoost Regressor for 15-min demand horizon...")
    model_15 = XGBRegressor(n_estimators=120, max_depth=6, learning_rate=0.08, random_state=42)
    model_15.fit(X_train, y15_train)
    preds_15 = model_15.predict(X_test)
    r2_15 = r2_score(y15_test, preds_15)
    mae_15 = mean_absolute_error(y15_test, preds_15)
    print(f"15-min Forecast MAE: {mae_15:.2f}, R2: {r2_15:.2f}")

    print("Training XGBoost Regressor for 30-min demand horizon...")
    model_30 = XGBRegressor(n_estimators=120, max_depth=6, learning_rate=0.08, random_state=42)
    model_30.fit(X_train, y30_train)

    print("Training XGBoost Regressor for 60-min demand horizon...")
    model_60 = XGBRegressor(n_estimators=120, max_depth=6, learning_rate=0.08, random_state=42)
    model_60.fit(X_train, y60_train)

    artifact = {
        "features": feature_cols,
        "model_15": model_15,
        "model_30": model_30,
        "model_60": model_60,
        "metrics": {"r2_15": round(r2_15, 3), "mae_15": round(mae_15, 3)},
        "dataset_rows": len(df),
    }

    output_path = os.path.join(SAVED_MODELS_DIR, "demand_forecaster.joblib")
    joblib.dump(artifact, output_path)
    print(f"Saved demand forecasting models to {output_path}")
    return artifact


if __name__ == "__main__":
    train_demand_forecasting_models()
