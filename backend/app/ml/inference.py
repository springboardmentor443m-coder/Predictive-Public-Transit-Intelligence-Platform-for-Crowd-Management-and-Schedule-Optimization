import os
import joblib
import torch
import numpy as np
import pandas as pd
from datetime import datetime, timedelta, timezone

from app.ml.data_generator import STATION_METADATA

SAVED_MODELS_DIR = os.path.join(os.path.dirname(__file__), "saved_models")


class MLInferenceEngine:
    def __init__(self):
        self.demand_model_data = None
        self.crowd_clf_data = None
        self.load_models()

    def load_models(self):
        demand_path = os.path.join(SAVED_MODELS_DIR, "demand_forecaster.joblib")
        if os.path.exists(demand_path):
            try:
                self.demand_model_data = joblib.load(demand_path)
            except Exception as e:
                print(f"Error loading demand model: {e}")

        crowd_path = os.path.join(SAVED_MODELS_DIR, "crowd_classifier.joblib")
        if os.path.exists(crowd_path):
            try:
                self.crowd_clf_data = joblib.load(crowd_path)
            except Exception as e:
                print(f"Error loading crowd classifier model: {e}")

    def forecast_station_demand(
        self, 
        station_id: int, 
        current_inflow: int, 
        current_outflow: int, 
        current_density: float,
        horizon_minutes: int = 30
    ) -> dict:
        now = datetime.now(timezone.utc)
        station_info = next((s for s in STATION_METADATA if s["id"] == station_id), STATION_METADATA[0])
        
        # Build feature vector
        features = pd.DataFrame([{
            "station_id": station_id,
            "hour": now.hour,
            "minute": now.minute,
            "day_of_week": now.weekday(),
            "is_weekend": int(now.weekday() >= 5),
            "capacity": station_info["capacity"],
            "inflow_ppm": current_inflow,
            "outflow_ppm": current_outflow,
            "line_delay_min": 0,
            "density_pct": current_density,
        }])

        predicted_inflow = current_inflow
        if self.demand_model_data:
            m_key = f"model_{horizon_minutes}" if horizon_minutes in (15, 30, 60) else "model_30"
            model = self.demand_model_data.get(m_key)
            if model:
                try:
                    pred = model.predict(features)[0]
                    predicted_inflow = max(10, int(pred))
                except Exception:
                    pass

        # Generate future time-series points
        forecast_points = []
        steps = horizon_minutes // 5 if horizon_minutes >= 15 else 3
        for i in range(1, steps + 1):
            future_time = now + timedelta(minutes=i * 5)
            trend_factor = 1.0 + (0.05 * (1 if now.hour in (8, 9, 17, 18) else -0.02) * i)
            pt_inflow = max(10, int(predicted_inflow * trend_factor))
            pt_outflow = max(8, int(current_outflow * trend_factor * 0.95))
            
            lower_bound = max(5, int(pt_inflow * 0.88))
            upper_bound = int(pt_inflow * 1.12)
            surge_prob = min(0.98, max(0.05, (current_density / 100.0) * trend_factor))

            forecast_points.append({
                "timestamp": future_time.strftime("%H:%M"),
                "predicted_inflow": pt_inflow,
                "predicted_outflow": pt_outflow,
                "confidence_interval_lower": lower_bound,
                "confidence_interval_upper": upper_bound,
                "surge_probability": round(surge_prob, 2),
            })

        predicted_peak_density = min(99.0, round(current_density * (1.1 if now.hour in (8, 9, 17, 18) else 0.95), 1))
        risk_level = "CRITICAL" if predicted_peak_density > 80 else ("MODERATE" if predicted_peak_density > 60 else "LOW")

        return {
            "station_id": station_id,
            "station_name": station_info["name"],
            "line_name": station_info["line"],
            "forecast_horizon_minutes": horizon_minutes,
            "current_density_pct": current_density,
            "predicted_peak_density_pct": predicted_peak_density,
            "risk_level": risk_level,
            "surge_probability": round(min(0.95, current_density / 90.0), 2),
            "forecast_points": forecast_points,
        }


ml_inference = MLInferenceEngine()
