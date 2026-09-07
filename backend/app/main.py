import json
import os
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import joblib
import pandas as pd

app = FastAPI(title="MetroFlow Intelligence Platform")

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "demand_forecast_model.pkl")
model = joblib.load(MODEL_PATH) if os.path.exists(MODEL_PATH) else None

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class LoginRequest(BaseModel):
    username: str
    password: str

class ForecastRequest(BaseModel):
    target_hour: int
    day_of_week: int

@app.post("/api/v1/auth/login")
def login(creds: LoginRequest):
    if creds.username == "operator" and creds.password == "metro123":
        return {"status": "success", "token": "session-token-xyz", "role": "operator"}
    return {"status": "error", "message": "Invalid username or password"}

@app.get("/api/v1/crowd/live")
def get_live_crowd():
    path = os.path.join(os.path.dirname(__file__), "..", "data", "live_crowd_summary.csv")
    if os.path.exists(path):
        df = pd.read_csv(path)
        return df.fillna(0).to_dict(orient="records")
    return []

# Supports frontend POST inference
@app.post("/api/v1/predict/demand")
def predict_demand_post(req: ForecastRequest):
    if model is not None:
        prediction = model.predict([[req.target_hour, req.day_of_week]])[0]
        val = round(float(prediction), 2)
    else:
        # Fallback if model pkl is still training
        base = 920.0
        multiplier = 2.2 if (7 <= req.target_hour <= 9 or 17 <= req.target_hour <= 20) else 1.1
        val = round(base * multiplier, 2)
        
    risk = "HIGH PEAK" if val > 1800 else ("MODERATE PEAK" if val > 900 else "NORMAL")
    return {
        "predicted_inflow": val,
        "surge_risk": risk
    }

@app.get("/api/v1/prediction/demand")
def predict_demand(hour: int, day_of_week: int):
    if model is not None:
        prediction = model.predict([[hour, day_of_week]])[0]
        val = round(float(prediction), 2)
    else:
        val = 1450.0
    return {
        "hour": hour,
        "day_of_week": day_of_week,
        "predicted_demand": val
    }

@app.get("/api/v1/analytics/summary")
def analytics_summary():
    csv_path = os.path.join(os.path.dirname(__file__), "..", "data", "live_crowd_summary.csv")
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        return {
            "total_stations": len(df),
            "average_inflow": round(float(df["inflow"].mean()), 2),
            "average_outflow": round(float(df["outflow"].mean()), 2),
            "highest_crowd_station": str(df.loc[df["net_occupancy"].idxmax(), "station_id"]),
            "highest_net_occupancy": int(df["net_occupancy"].max())
        }
    return {}

@app.get("/api/v1/scheduling/timetable")
def get_train_timetables():
    path = os.path.join(os.path.dirname(__file__), "..", "data", "active_schedules.csv")
    if os.path.exists(path):
        return pd.read_csv(path).to_dict(orient="records")
    return []

@app.get("/api/v1/scheduling/frequency")
def get_frequency_adjustments():
    path = os.path.join(os.path.dirname(__file__), "..", "data", "frequency_recommendations.csv")
    if os.path.exists(path):
        return pd.read_csv(path).to_dict(orient="records")
    return []

@app.get("/api/v1/scheduling/peak-optimization")
def get_peak_hour_policy():
    path = os.path.join(os.path.dirname(__file__), "..", "data", "peak_hour_policy.csv")
    if os.path.exists(path):
        return pd.read_csv(path).to_dict(orient="records")
    return []

@app.get("/api/v1/operational/telemetry")
def get_operational_telemetry():
    path = os.path.join(os.path.dirname(__file__), "..", "data", "operational_telemetry.csv")
    if os.path.exists(path):
        return pd.read_csv(path).to_dict(orient="records")
    return []

@app.get("/api/v1/traffic/patterns")
def get_traffic_patterns():
    path = os.path.join(os.path.dirname(__file__), "..", "data", "traffic_patterns.csv")
    if os.path.exists(path):
        return pd.read_csv(path).to_dict(orient="records")
    return []

@app.get("/api/v1/traffic/report")
def get_traffic_report():
    path = os.path.join(os.path.dirname(__file__), "..", "data", "traffic_analysis_report.json")
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return {"error": "Report not generated yet"}

@app.get("/api/v1/ai/recommendations")
def get_ai_recommendations():
    path = os.path.join(os.path.dirname(__file__), "..", "data", "ai_recommendations.csv")
    if os.path.exists(path):
        return pd.read_csv(path).to_dict(orient="records")
    return []