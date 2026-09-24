"""
AI Prediction Module
- Crowd prediction models / passenger demand forecasting (RandomForest)
- Delay impact prediction (new, Week 3&4 -- uses the delay dataset)
- Traffic pattern analysis / smart recommendations
"""
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

from app.data import repository as repo

MODEL_DIR = Path(__file__).resolve().parents[1] / "ml_artifacts"
MODEL_DIR.mkdir(exist_ok=True)
DEMAND_MODEL_PATH = MODEL_DIR / "crowd_prediction_model.joblib"
DELAY_MODEL_PATH = MODEL_DIR / "delay_prediction_model.joblib"
ENCODER_PATH = MODEL_DIR / "station_encoder.joblib"


def _build_features(df: pd.DataFrame, encoder: LabelEncoder) -> pd.DataFrame:
    return pd.DataFrame({
        "station_enc": encoder.transform(df["Station"]),
        "hour": df["Hour"],
        "day_of_week": df["day_of_week"],
        "month": df["month"],
        "is_weekend": df["is_weekend"].astype(int),
    })


def train_demand_model() -> dict:
    df = repo.load_data()
    encoder = LabelEncoder()
    encoder.fit(df["Station"])

    X = _build_features(df, encoder)
    y = df["Entries"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = RandomForestRegressor(n_estimators=150, max_depth=14, min_samples_leaf=3, n_jobs=-1, random_state=42)
    model.fit(X_train, y_train)
    preds = model.predict(X_test)
    mae = mean_absolute_error(y_test, preds)
    mape = float(np.mean(np.abs((y_test - preds) / np.maximum(y_test, 1))) * 100)

    joblib.dump(model, DEMAND_MODEL_PATH)
    joblib.dump(encoder, ENCODER_PATH)
    return {"trained_rows": len(df), "mae": round(mae, 2), "mape_pct": round(mape, 2)}


def train_delay_model() -> dict:
    """Predicts expected delay minutes for a station-hour, trained on the
    delay log (which is itself congestion-correlated -- see generate_dataset.py)."""
    ridership = repo.load_data()
    delays = repo.load_delays()

    merged = ridership.merge(delays, on=["Date", "Hour", "Station"], how="left")
    merged["DelayMinutes"] = merged["DelayMinutes"].fillna(0.0)

    encoder = joblib.load(ENCODER_PATH) if ENCODER_PATH.exists() else LabelEncoder().fit(merged["Station"])
    X = _build_features(merged, encoder)
    y = merged["DelayMinutes"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = RandomForestRegressor(n_estimators=120, max_depth=10, min_samples_leaf=5, n_jobs=-1, random_state=42)
    model.fit(X_train, y_train)
    preds = model.predict(X_test)
    mae = mean_absolute_error(y_test, preds)

    joblib.dump(model, DELAY_MODEL_PATH)
    return {"trained_rows": len(merged), "mae_minutes": round(mae, 2)}


def _load_demand_model():
    if not DEMAND_MODEL_PATH.exists():
        train_demand_model()
    return joblib.load(DEMAND_MODEL_PATH), joblib.load(ENCODER_PATH)


def _load_delay_model():
    if not DELAY_MODEL_PATH.exists():
        train_delay_model()
    return joblib.load(DELAY_MODEL_PATH)


def _feature_row(station: str, date: str, hour: int, encoder: LabelEncoder) -> pd.DataFrame:
    dt = pd.to_datetime(date)
    return pd.DataFrame({
        "station_enc": [encoder.transform([station])[0]],
        "hour": [hour],
        "day_of_week": [dt.dayofweek],
        "month": [dt.month],
        "is_weekend": [int(dt.dayofweek >= 5)],
    })


def predict_demand(station: str, date: str, hour: int) -> dict:
    model, encoder = _load_demand_model()
    row = _feature_row(station, date, hour, encoder)
    pred = float(model.predict(row)[0])
    cap = repo.get_capacity(station)
    congestion_pct = round(min(100, (pred / cap) * 100), 1)
    return {
        "station": station, "date": date, "hour": hour,
        "predicted_entries": round(pred, 1),
        "predicted_congestion_pct": congestion_pct,
    }


def predict_delay(station: str, date: str, hour: int) -> dict:
    """Delay impact prediction -- Week 3&4 addition."""
    delay_model = _load_delay_model()
    _, encoder = _load_demand_model()
    row = _feature_row(station, date, hour, encoder)
    pred_minutes = max(0.0, float(delay_model.predict(row)[0]))
    return {"station": station, "date": date, "hour": hour, "predicted_delay_minutes": round(pred_minutes, 1)}


def forecast_peak_hours(station: str, date: str) -> list[dict]:
    return [predict_demand(station, date, h) for h in range(24)]


def forecast_delays(station: str, date: str) -> list[dict]:
    return [predict_delay(station, date, h) for h in range(24)]


def smart_recommendations(station: str, date: str) -> list[str]:
    demand = forecast_peak_hours(station, date)
    delays = {d["hour"]: d["predicted_delay_minutes"] for d in forecast_delays(station, date)}
    recs = []
    for f in demand:
        h = f["hour"]
        delay = delays.get(h, 0)
        if f["predicted_congestion_pct"] >= 90:
            recs.append(
                f"{station} @ {h:02d}:00 - CRITICAL demand ({f['predicted_congestion_pct']}%), "
                f"expected delay ~{delay} min. Recommend increasing train frequency."
            )
        elif f["predicted_congestion_pct"] >= 70:
            recs.append(
                f"{station} @ {h:02d}:00 - High demand ({f['predicted_congestion_pct']}%), "
                f"expected delay ~{delay} min. Consider additional platform staff."
            )
    if not recs:
        recs.append(f"{station} - no critical congestion or delays predicted for {date}.")
    return recs


def train_all_models() -> dict:
    demand_metrics = train_demand_model()
    delay_metrics = train_delay_model()
    return {"demand_model": demand_metrics, "delay_model": delay_metrics}
