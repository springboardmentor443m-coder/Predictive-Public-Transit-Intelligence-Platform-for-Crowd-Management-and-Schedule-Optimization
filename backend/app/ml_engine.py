import os
import joblib
import pandas as pd
import numpy as np

MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "crowd_model.pkl")
ENCODER_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "encoders.pkl")

class CrowdPredictor:
    def __init__(self):
        self.model = None
        self.station_encoder = None
        self.load_model()

    def load_model(self):
        if os.path.exists(MODEL_PATH) and os.path.exists(ENCODER_PATH):
            self.model = joblib.load(MODEL_PATH)
            encoders = joblib.load(ENCODER_PATH)
            self.station_encoder = encoders["station_encoder"]
        else:
            self.model = None

    def predict_crowd(self, station_id: str, day_of_week: int, hour_of_day: int, max_capacity: int = 1000):
        if not self.model or not self.station_encoder:
            return {"error": "Model not loaded. Please train model first."}

        try:
            stn_encoded = self.station_encoder.transform([station_id])[0]
        except Exception:
            stn_encoded = 0

        is_weekend = 1 if day_of_week >= 5 else 0
        is_peak = 1 if (hour_of_day in [8, 9, 10, 17, 18, 19] and not is_weekend) else 0

        input_data = pd.DataFrame([{
            "station_encoded": stn_encoded,
            "day_of_week": day_of_week,
            "hour_of_day": hour_of_day,
            "is_weekend": is_weekend,
            "is_peak_hour": is_peak
        }])

        predicted_occupancy = int(self.model.predict(input_data)[0])
        cap_pct = round((predicted_occupancy / max_capacity) * 100, 1)

        if cap_pct >= 85:
            risk = "Critical Overcrowding"
            rec_trains = "+3 Extra Trains (Frequency: 3 mins)"
            action = "Limit platform turnstile entries & dispatch emergency standby train immediately."
        elif cap_pct >= 70:
            risk = "High Density"
            rec_trains = "+1-2 Extra Trains (Frequency: 4 mins)"
            action = "Increase train frequency and issue automated platform announcements."
        elif cap_pct >= 45:
            risk = "Moderate Crowd"
            rec_trains = "Standard Schedule (Frequency: 6 mins)"
            action = "Maintain normal timetable monitoring."
        else:
            risk = "Low Crowd"
            rec_trains = "Off-Peak Schedule (Frequency: 8-10 mins)"
            action = "Energy saving mode / Standard operations."

        return {
            "station_id": station_id,
            "day_of_week": day_of_week,
            "hour_of_day": hour_of_day,
            "predicted_occupancy": predicted_occupancy,
            "capacity_pct": cap_pct,
            "risk_level": risk,
            "recommended_train_frequency": rec_trains,
            "recommended_action": action
        }

predictor = CrowdPredictor()
