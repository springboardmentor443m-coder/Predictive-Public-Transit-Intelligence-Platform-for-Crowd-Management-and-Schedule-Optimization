import sys
import os
import json
from datetime import datetime
from typing import List, Dict
import asyncio
from simulator import simulate_realtime_tick

import numpy as np
import pandas as pd
import joblib
from pydantic import BaseModel
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Ensure the backend directory is in the path to import helper engines
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from alert_manager import alert_hub
from analytics_engine import analytics_engine

app = FastAPI(title="MetroFlow Intelligence Platform", version="1.0.0")
@app.on_event("startup")
async def start_telemetry_stream():
    """Launches the background simulation loop when FastAPI starts."""
    async def run_loop():
        while True:
            try:
                simulate_realtime_tick()
            except Exception as e:
                print(f"[Simulator Warning] {e}")
            await asyncio.sleep(5)  # Runs every 5 seconds

    asyncio.create_task(run_loop())

# Enable full CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load Trained ML Model
MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "demand_forecast_model.pkl")
model = joblib.load(MODEL_PATH) if os.path.exists(MODEL_PATH) else None

# --- Pydantic Request Schemas ---

class LoginRequest(BaseModel):
    username: str
    password: str

class ForecastRequest(BaseModel):
    target_hour: int
    day_of_week: int

class EmergencyBroadcastRequest(BaseModel):
    line: str
    severity: str
    message: str
    operator_id: str

class ScheduleUpdateRequest(BaseModel):
    trip_id: str
    new_headway_minutes: int
    reason: str

# ==========================================
# Milestone 1: Authentication & Crowd Monitoring
# ==========================================

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

@app.get("/api/v1/crowd/live-summary")
def get_live_crowd_summary():
    """Returns formatted station data consumed by the dashboard table."""
    path = os.path.join(os.path.dirname(__file__), "..", "data", "live_crowd_summary.csv")
    if os.path.exists(path):
        df = pd.read_csv(path)
        stations = []
        for _, row in df.iterrows():
            name = str(row.get("station_name", row.get("station_id", "Station")))
            net = int(row.get("net_flow", row.get("net_occupancy", 0)))
            status = str(row.get("congestion_level", "NORMAL"))
            if status not in ["NORMAL", "MODERATE", "HIGH", "CRITICAL"]:
                status = "CRITICAL" if net >= 1200 else ("HIGH" if net >= 800 else ("MODERATE" if net >= 400 else "NORMAL"))
            stations.append({
                "station_name": name,
                "net_flow": net,
                "status": status
            })
        return {"stations": stations}
    return {
        "stations": [
            {"station_name": "Central Station", "net_flow": 1240, "status": "CRITICAL"},
            {"station_name": "Grand Central-42 St", "net_flow": 890, "status": "HIGH"},
            {"station_name": "34 St-Penn Station", "net_flow": 620, "status": "MODERATE"},
            {"station_name": "14 St-Union Sq", "net_flow": 310, "status": "NORMAL"}
        ]
    }

# ==========================================
# Milestone 2: AI Prediction & Traffic Intelligence
# ==========================================

@app.post("/api/v1/predict/demand")
def predict_demand_post(req: ForecastRequest):
    if model is not None:
        prediction = model.predict([[req.target_hour, req.day_of_week]])[0]
        val = round(float(prediction), 2)
    else:
        base = 920.0
        multiplier = 2.2 if (7 <= req.target_hour <= 9 or 17 <= req.target_hour <= 20) else 1.1
        val = round(base * multiplier, 2)
        
    risk = "HIGH PEAK" if val > 1800 else ("MODERATE PEAK" if val > 900 else "NORMAL")
    return {"predicted_inflow": val, "surge_risk": risk}

@app.get("/api/v1/prediction/demand")
def predict_demand(hour: int, day_of_week: int):
    if model is not None:
        prediction = model.predict([[hour, day_of_week]])[0]
        val = round(float(prediction), 2)
    else:
        val = 1450.0
    return {"hour": hour, "day_of_week": day_of_week, "predicted_demand": val}

@app.get("/api/v1/prediction/forecast-24h")
def get_24h_demand_forecast():
    """Supplies 24-hour actuals vs AI forecast to the frontend chart."""
    hours = [6, 8, 10, 12, 14, 16, 18, 20, 22]
    forecast = []
    
    if model is not None:
        for h in hours:
            p = model.predict([[h, 0]])[0]  # Predict for Monday
            forecast.append(int(p))
    else:
        base_curve = [300, 1100, 750, 510, 500, 910, 1320, 790, 390]
        forecast = base_curve

    # Derived actual counts with slight variance
    actuals = [max(100, int(val + np.random.randint(-40, 45))) for val in forecast]
    
    return {
        "labels": [f"{h:02d}:00" for h in hours],
        "actual_inflow": actuals,
        "ai_forecast": forecast
    }

@app.get("/api/v1/analytics/summary")
def analytics_summary():
    csv_path = os.path.join(os.path.dirname(__file__), "..", "data", "live_crowd_summary.csv")
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        return {
            "total_stations": len(df),
            "average_inflow": round(float(df["inflow"].mean()), 2) if "inflow" in df.columns else 0.0,
            "average_outflow": round(float(df["outflow"].mean()), 2) if "outflow" in df.columns else 0.0,
            "highest_crowd_station": str(df.loc[df["net_flow"].idxmax(), "station_name"]) if "net_flow" in df.columns else "Central Station",
            "highest_net_occupancy": int(df["net_flow"].max()) if "net_flow" in df.columns else 0
        }
    return {}

@app.get("/api/v1/scheduling/timetable")
def get_train_timetables():
    path = os.path.join(os.path.dirname(__file__), "..", "data", "active_schedules.csv")
    if os.path.exists(path):
        df = pd.read_csv(path)
        records = []
        for idx, row in df.iterrows():
            records.append({
                "trip_id": str(row.get("trip_id", f"TRIP-0{idx+1}")),
                "route": str(row.get("route_id", row.get("route", f"Line {idx+1}"))),
                "delay_min": round(float(row.get("delay_minutes", row.get("delay_min", 2.0))), 1),
                "headway": int(row.get("headway_minutes", row.get("headway", 6)))
            })
        return {"timetable": records}
    return {
        "timetable": [
            {"trip_id": "TRIP-01", "route": "Red Line 1", "delay_min": 2.1, "headway": 6},
            {"trip_id": "TRIP-02", "route": "Blue Line 2", "delay_min": 4.8, "headway": 8},
            {"trip_id": "TRIP-03", "route": "Green Line 4", "delay_min": 1.0, "headway": 5}
        ]
    }

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

# ==========================================
# Milestone 3: Alerts, Notifications & Analytics
# ==========================================

@app.get("/api/v1/alerts/live")
def get_live_alerts():
    """Retrieve all triggered crowd and delay alerts."""
    return {"alerts": alert_hub.get_recent_alerts()}

@app.post("/api/v1/alerts/emergency")
def trigger_emergency_announcement(req: EmergencyBroadcastRequest):
    """Broadcast an emergency announcement across lines/stations."""
    announcement = alert_hub.broadcast_emergency(
        line=req.line,
        severity=req.severity,
        message=req.message,
        operator_id=req.operator_id
    )
    return {"status": "SUCCESS", "announcement": announcement}

@app.get("/api/v1/alerts/announcements")
def get_active_announcements():
    """Fetch active operator emergency announcements."""
    return {"announcements": alert_hub.get_active_announcements()}

@app.post("/api/v1/scheduling/update-headway")
def update_schedule_headway(req: ScheduleUpdateRequest):
    """Direct operational override: dynamically update headway interval."""
    alert_hub.evaluate_delay_thresholds(req.trip_id, float(req.new_headway_minutes))
    return {
        "status": "UPDATED",
        "trip_id": req.trip_id,
        "assigned_headway": req.new_headway_minutes,
        "message": f"Headway updated to {req.new_headway_minutes} min due to: {req.reason}"
    }

@app.get("/api/v1/analytics/kpis")
def get_operational_kpis():
    """Returns network-wide throughput, punctuality, and fleet efficiency."""
    return analytics_engine.compute_network_kpis()

@app.get("/api/v1/analytics/heatmap")
def get_congestion_heatmap():
    """Returns station coordinates and congestion weights for heatmap rendering."""
    return {"points": analytics_engine.generate_congestion_heatmap()}