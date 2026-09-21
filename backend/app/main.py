import os
import sqlite3
from datetime import datetime
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from app.ml_engine import predictor
from app.data_generator import generate_datasets, seed_database

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "metroflow.db")

app = FastAPI(title="MetroFlow AI Platform API", version="1.3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Models
class LoginRequest(BaseModel):
    username: str
    password: str

class PredictRequest(BaseModel):
    station_id: str
    day_of_week: int
    hour_of_day: int

class UpdateTrainRequest(BaseModel):
    frequency: int
    delay: int
    status: str

class UpdateOccupancyRequest(BaseModel):
    current_occupancy: int

@app.on_event("startup")
def startup_event():
    if not os.path.exists(DB_PATH):
        generate_datasets()
        seed_database()

@app.get("/")
def read_root():
    return {"status": "MetroFlow API is running", "version": "1.3.0"}

@app.post("/api/auth/login")
def login(req: LoginRequest):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, username, role, full_name FROM users WHERE username = ? AND password = ?", (req.username, req.password))
    user = cursor.fetchone()
    db.close()
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    assigned_station = "STN_001" if user["role"] == "operator" else None
    
    return {
        "status": "success",
        "user": {
            "id": user["id"],
            "username": user["username"],
            "role": user["role"],
            "full_name": user["full_name"],
            "assigned_station": assigned_station
        }
    }

@app.get("/api/stations")
def get_stations():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM stations")
    rows = cursor.fetchall()
    db.close()
    
    stations = []
    for r in rows:
        pct = round((r["current_occupancy"] / r["capacity"]) * 100, 1)
        cg = "Critical" if pct >= 85 else ("High" if pct >= 70 else ("Medium" if pct >= 45 else "Low"))
        stations.append({
            "id": r["id"],
            "name": r["name"],
            "line": r["line"],
            "capacity": r["capacity"],
            "current_occupancy": r["current_occupancy"],
            "occupancy_pct": pct,
            "congestion_level": cg,
            "lat": r["lat"],
            "lng": r["lng"]
        })
    return stations

@app.put("/api/stations/{station_id}/occupancy")
def update_station_occupancy(station_id: str, req: UpdateOccupancyRequest):
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("SELECT name, capacity FROM stations WHERE id = ?", (station_id,))
    stn = cursor.fetchone()
    
    if not stn:
        db.close()
        raise HTTPException(status_code=404, detail="Station not found")
        
    stn_name = stn["name"]
    capacity = stn["capacity"]
    pct = round((req.current_occupancy / capacity) * 100, 1)
    
    cg = "Critical" if pct >= 85 else ("High" if pct >= 70 else ("Medium" if pct >= 45 else "Low"))
    
    cursor.execute("UPDATE stations SET current_occupancy = ?, congestion_level = ? WHERE id = ?", (req.current_occupancy, cg, station_id))
    
    if pct >= 85:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        msg = f"CRITICAL OVERCROWD ALERT: {stn_name} reached {pct}% capacity ({req.current_occupancy}/{capacity} passengers)! High rush at turnstile gates."
        cursor.execute(
            "INSERT INTO alerts (station_name, severity, message, timestamp, resolved) VALUES (?, 'Critical', ?, ?, 0)",
            (stn_name, msg, now_str)
        )
    
    db.commit()
    db.close()
    return {"status": "success", "message": f"Updated occupancy for {station_id}", "capacity_pct": pct, "congestion_level": cg}

@app.get("/api/trains")
def get_trains():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM trains")
    rows = cursor.fetchall()
    db.close()
    return [dict(r) for r in rows]

@app.put("/api/trains/{train_id}")
def update_train(train_id: str, req: UpdateTrainRequest):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "UPDATE trains SET frequency = ?, delay = ?, status = ? WHERE id = ?",
        (req.frequency, req.delay, req.status, train_id)
    )
    
    if req.delay > 5:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("SELECT line, origin, destination FROM trains WHERE id = ?", (train_id,))
        trn = cursor.fetchone()
        trn_info = f"{train_id} ({trn['line']}: {trn['origin']} -> {trn['destination']})" if trn else train_id
        msg = f"TRAIN DELAY WARNING: Train {trn_info} delayed by {req.delay} minutes due to signal traffic."
        cursor.execute(
            "INSERT INTO alerts (station_name, severity, message, timestamp, resolved) VALUES (?, 'Warning', ?, ?, 0)",
            (trn['origin'] if trn else 'Network', msg, now_str)
        )
        
    db.commit()
    db.close()
    return {"status": "success", "message": f"Updated train {train_id}"}

@app.post("/api/predict")
def predict_crowd(req: PredictRequest):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT capacity FROM stations WHERE id = ?", (req.station_id,))
    stn = cursor.fetchone()
    db.close()
    
    max_cap = stn["capacity"] if stn else 1000
    res = predictor.predict_crowd(req.station_id, req.day_of_week, req.hour_of_day, max_cap)
    return res

@app.get("/api/alerts")
def get_alerts():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM alerts WHERE resolved = 0 ORDER BY id DESC LIMIT 15")
    rows = cursor.fetchall()
    db.close()
    return [dict(r) for r in rows]

@app.post("/api/alerts/{alert_id}/resolve")
def resolve_alert(alert_id: int):
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("SELECT station_name FROM alerts WHERE id = ?", (alert_id,))
    alert = cursor.fetchone()
    
    cursor.execute("UPDATE alerts SET resolved = 1 WHERE id = ?", (alert_id,))
    
    # DYNAMIC DENSITY RESET: Resolving alert lowers station occupancy back to 50% normal level!
    if alert and alert["station_name"]:
        stn_name = alert["station_name"]
        cursor.execute("SELECT id, capacity FROM stations WHERE name = ?", (stn_name,))
        stn = cursor.fetchone()
        if stn:
            normal_occ = int(stn["capacity"] * 0.5) # 50% capacity (Normal green status)
            cursor.execute("UPDATE stations SET current_occupancy = ?, congestion_level = 'Low' WHERE id = ?", (normal_occ, stn["id"]))
            
    db.commit()
    db.close()
    return {"status": "success", "message": f"Alert {alert_id} resolved and station density reset to normal."}

@app.get("/api/analytics")
def get_analytics(station_id: Optional[str] = Query(None)):
    db = get_db()
    cursor = db.cursor()
    
    if station_id and station_id != "ALL":
        cursor.execute("SELECT name, line FROM stations WHERE id = ?", (station_id,))
        stn = cursor.fetchone()
        stn_name = stn["name"] if stn else "Selected Station"
        stn_line = stn["line"] if stn else "Metro Line"
        
        cursor.execute("""
            SELECT hour_of_day, CAST(ROUND(AVG(current_occupancy)) AS INTEGER) as avg_passengers 
            FROM ridership_logs 
            WHERE station_id = ? 
            GROUP BY hour_of_day 
            ORDER BY hour_of_day
        """, (station_id,))
        rows = cursor.fetchall()
        
        hourly_data = [
            {"hour": f"{r['hour_of_day']:02d}:00", "passengers": r["avg_passengers"]}
            for r in rows
        ]
        
        cursor.execute("SELECT SUM(entry_count) as total FROM ridership_logs WHERE station_id = ?", (station_id,))
        tot = cursor.fetchone()
        total_daily = tot["total"] if tot and tot["total"] else 3200
        
        db.close()
        return {
            "selected_station": stn_name,
            "total_daily_ridership": total_daily,
            "peak_hour": "08:00 - 10:00" if station_id in ["STN_001", "STN_002"] else "17:00 - 19:00",
            "hub_focus_label": "Station Metro Line",
            "busiest_station": stn_line,
            "avg_delay_mins": 0.8,
            "hourly_distribution": hourly_data
        }
    else:
        cursor.execute("""
            SELECT hour_of_day, CAST(ROUND(SUM(current_occupancy)) AS INTEGER) as total_passengers 
            FROM ridership_logs 
            GROUP BY hour_of_day 
            ORDER BY hour_of_day
        """)
        rows = cursor.fetchall()
        
        hourly_data = [
            {"hour": f"{r['hour_of_day']:02d}:00", "passengers": r["total_passengers"]}
            for r in rows
        ]
        
        cursor.execute("SELECT SUM(entry_count) as total FROM ridership_logs")
        tot = cursor.fetchone()
        total_daily = tot["total"] if tot and tot["total"] else 18500
        
        db.close()
        return {
            "selected_station": "All Network Stations",
            "total_daily_ridership": total_daily,
            "peak_hour": "18:00 - 19:00",
            "hub_focus_label": "Busiest Network Hub",
            "busiest_station": "Central Hub",
            "avg_delay_mins": 1.4,
            "hourly_distribution": hourly_data
        }
