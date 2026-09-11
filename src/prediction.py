"""
prediction.py — Inference API for the Streamlit passenger and operator pages.

This module is the only place that loads the trained model from disk.
All UI pages call predict_demand() instead of touching joblib directly.

Why separate inference from training?
- If the model is retrained, only train_model.py changes; the UI doesn't.
- The UI can gracefully catch ModelNotFoundError instead of crashing.
- Keeps the model loading overhead to a single cached call (via Streamlit cache).
"""

import sys
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import joblib
import numpy as np

from src.config import (
    MODEL_PATH,
    MODEL_METADATA_PATH,
    ROUTES,
    DEFAULT_VEHICLE_CAPACITY,
)
from src.feature_engineering import build_inference_row


class ModelNotFoundError(Exception):
    """Raised when the model file hasn't been trained yet."""
    pass


def load_model() -> dict:
    """
    Load the saved model bundle from disk.

    Returns
    -------
    dict with keys: 'model' (fitted estimator), 'route_encoder' (LabelEncoder)

    Raises
    ------
    ModelNotFoundError
        If models/best_model.joblib does not exist.
    """
    if not MODEL_PATH.exists():
        raise ModelNotFoundError(
            f"No trained model found at {MODEL_PATH}.\n"
            "Please run: python src/train_model.py"
        )
    return joblib.load(MODEL_PATH)


def load_metadata() -> dict:
    """
    Load model training metadata (metrics, feature importance, etc.).

    Returns an empty dict if the metadata file doesn't exist —
    the UI handles that gracefully.
    """
    if not MODEL_METADATA_PATH.exists():
        return {}
    with open(MODEL_METADATA_PATH, "r") as f:
        return json.load(f)


def predict_demand(
    route: str,
    hour: int,
    day_of_week: int,
    temperature: float,
    is_raining: int,
    nearby_event: int,
    prev_passenger_count: float,
    route_avg_demand: float,
    model_bundle: dict = None,
) -> float:
    """
    Predict passenger count for a single input scenario.

    Parameters
    ----------
    route               : Route name (must match training data names)
    hour                : Hour of day (0–23)
    day_of_week         : 0=Monday … 6=Sunday
    temperature         : Temperature in °C
    is_raining          : 1 if raining, 0 otherwise
    nearby_event        : 1 if a nearby event, 0 otherwise
    prev_passenger_count: Passenger count in the previous hour
    route_avg_demand    : Historical average demand for this route
    model_bundle        : Optional pre-loaded model dict (avoids re-loading)

    Returns
    -------
    float : Predicted passenger count (always non-negative)

    Raises
    ------
    ModelNotFoundError : if model file is missing
    """
    if model_bundle is None:
        model_bundle = load_model()

    model         = model_bundle["model"]
    route_encoder = model_bundle["route_encoder"]

    feature_row = build_inference_row(
        route=route,
        hour=hour,
        day_of_week=day_of_week,
        temperature=temperature,
        is_raining=is_raining,
        nearby_event=nearby_event,
        prev_passenger_count=prev_passenger_count,
        route_avg_demand=route_avg_demand,
        route_encoder=route_encoder,
    )

    prediction = model.predict(feature_row)[0]
    return max(0.0, round(float(prediction), 1))


def get_route_avg_demand(route: str, df=None) -> float:
    """
    Return the historical average demand for a route.
    If a dataframe is provided, compute from it; otherwise use a safe default.
    """
    if df is not None and len(df) > 0:
        route_data = df[df["route"] == route]
        if len(route_data) > 0:
            return float(route_data["passenger_count"].mean())
    # Fallback default (mid-range assumption)
    return 35.0


def predict_hourly_profile(
    route: str,
    day_of_week: int,
    temperature: float,
    is_raining: int,
    nearby_event: int,
    route_avg_demand: float,
    model_bundle: dict,
) -> list[dict]:
    """
    Predict demand for all 24 hours of a day for a given route/condition.
    Used by the passenger dashboard to show alternative travel times.

    Returns
    -------
    list of dicts: [{"hour": 0, "predicted_count": 12.5, "utilisation": 0.125}, ...]
    """
    capacity = ROUTES.get(route, DEFAULT_VEHICLE_CAPACITY)
    results  = []

    # Use prediction of current hour as prev_count for first hour;
    # then carry forward as a simple lag approximation.
    prev_count = route_avg_demand

    for h in range(24):
        count = predict_demand(
            route=route,
            hour=h,
            day_of_week=day_of_week,
            temperature=temperature,
            is_raining=is_raining,
            nearby_event=nearby_event,
            prev_passenger_count=prev_count,
            route_avg_demand=route_avg_demand,
            model_bundle=model_bundle,
        )
        results.append({
            "hour":            h,
            "predicted_count": count,
            "utilisation":     round(count / capacity, 4),
        })
        prev_count = count   # roll forward

    return results


if __name__ == "__main__":
    print("Testing prediction.py …")
    bundle = load_model()
    meta   = load_metadata()

    test = predict_demand(
        route="Route 1 - City Centre Express",
        hour=8,
        day_of_week=0,       # Monday
        temperature=22.0,
        is_raining=0,
        nearby_event=0,
        prev_passenger_count=50,
        route_avg_demand=55,
        model_bundle=bundle,
    )
    print(f"Test prediction (Route 1, 08:00 Mon): {test} passengers")
    print(f"Best model : {meta.get('best_model', 'unknown')}")
    print(f"Metrics    : {meta.get('best_metrics', {})}")
