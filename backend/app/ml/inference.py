import os
import joblib
import numpy as np
import pandas as pd
from datetime import datetime, timedelta, timezone

from app.ml.data_generator import STATION_METADATA

SAVED_MODELS_DIR = os.path.join(os.path.dirname(__file__), "saved_models")


class MLInferenceEngine:
    def __init__(self):
        self.demand_model_data = None
        self.iso_forest = None
        self.station_clusters = None
        self.load_models()

    def load_models(self):
        demand_path = os.path.join(SAVED_MODELS_DIR, "demand_forecaster.joblib")
        if os.path.exists(demand_path):
            try:
                self.demand_model_data = joblib.load(demand_path)
            except Exception as e:
                print(f"Error loading demand model: {e}")

        iso_path = os.path.join(SAVED_MODELS_DIR, "isolation_forest.joblib")
        if os.path.exists(iso_path):
            try:
                self.iso_forest = joblib.load(iso_path)
            except Exception as e:
                print(f"Error loading isolation forest: {e}")

        cluster_path = os.path.join(SAVED_MODELS_DIR, "station_clusters.joblib")
        if os.path.exists(cluster_path):
            try:
                self.station_clusters = joblib.load(cluster_path)
            except Exception as e:
                print(f"Error loading station clusters: {e}")

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
        
        # Build feature vector matching XGBoost training features:
        # ['station_id', 'hour', 'day_of_week', 'is_weekend', 'lag_1h', 'lag_2h', 'rolling_mean_3h', 'rolling_max_3h']
        lag1 = float(max(0, current_inflow))
        lag2 = float(max(0, int(current_inflow * 0.95)))
        features = pd.DataFrame([{
            "station_id": station_id,
            "hour": now.hour,
            "day_of_week": now.weekday(),
            "is_weekend": int(now.weekday() >= 5),
            "lag_1h": lag1,
            "lag_2h": lag2,
            "rolling_mean_3h": lag1,
            "rolling_max_3h": lag1 * 1.05,
        }])

        predicted_inflow = current_inflow
        if self.demand_model_data:
            if horizon_minutes <= 60:
                model = self.demand_model_data.get("model_1h")
            elif horizon_minutes <= 120:
                model = self.demand_model_data.get("model_2h")
            else:
                model = self.demand_model_data.get("model_4h")

            if model:
                try:
                    pred = model.predict(features)[0]
                    predicted_inflow = max(10, int(pred))
                except Exception as e:
                    print(f"Prediction inference error: {e}")

        # Generate future time-series points
        forecast_points = []
        steps = max(2, horizon_minutes // 15)
        for i in range(1, steps + 1):
            future_time = now + timedelta(minutes=i * 15)
            step_factor = 1.0 + (0.02 * (1 if now.hour in (8, 9, 17, 18) else -0.01) * i)
            pt_inflow = max(10, int(predicted_inflow * step_factor))
            pt_outflow = max(8, int(current_outflow * step_factor * 0.96))
            
            lower_bound = max(5, int(pt_inflow * 0.88))
            upper_bound = int(pt_inflow * 1.12)
            surge_prob = min(0.98, max(0.05, (current_density / 100.0) * step_factor))

            forecast_points.append({
                "timestamp": future_time.strftime("%H:%M"),
                "predicted_inflow": pt_inflow,
                "predicted_outflow": pt_outflow,
                "confidence_interval_lower": lower_bound,
                "confidence_interval_upper": upper_bound,
                "surge_probability": round(surge_prob, 2),
            })

        predicted_peak_density = min(99.0, round(current_density * (1.1 if now.hour in (8, 9, 17, 18) else 0.95), 1))
        risk_level = "CRITICAL" if predicted_peak_density > 80 else ("MODERATE" if predicted_peak_density > 50 else "LOW")

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

