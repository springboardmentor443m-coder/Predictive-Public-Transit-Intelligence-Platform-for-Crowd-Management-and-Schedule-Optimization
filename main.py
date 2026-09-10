from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, Union, List, Dict, Any
import pandas as pd
import numpy as np
import xgboost as xgb
import traceback
import os
from pydantic import BaseModel, Field

app = FastAPI(
    title="MetroFlow: AI-Powered Metro Crowd Management & Scheduling API",
    description="Full-stack AI transit platform for live passenger prediction, fleet schedule advisory, and real-time overcrowding alerts.",
    version="1.0"
)

# ==========================================
# 0. CORS CONFIGURATION
# ==========================================
# Allow requests from React frontend on Vite (5173), CRA (3000), and all local ports
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# 1. METRO NETWORK ENCODINGS & CONSTANTS
# ==========================================
STATION_MAPPING = {
    'Botanical Garden': 0,
    'Dwarka Sec 21': 1,
    'Hauz Khas': 2,
    'Kashmere Gate': 3,
    'Rajiv Chowk': 4
}
INV_STATION_MAPPING = {v: k for k, v in STATION_MAPPING.items()}

LINE_MAPPING = {
    'Blue Line': 0,
    'Magenta Line': 1,
    'Red Line': 2,
    'Yellow Line': 3
}
INV_LINE_MAPPING = {v: k for k, v in LINE_MAPPING.items()}

DAY_MAPPING = {
    'Friday': 0,
    'Monday': 1,
    'Saturday': 2,
    'Sunday': 3,
    'Thursday': 4,
    'Tuesday': 5,
    'Wednesday': 6
}
INV_DAY_MAPPING = {v: k for k, v in DAY_MAPPING.items()}

DAY_INDEX_TO_NAME = [
    'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'
]

# ==========================================
# 2. LOAD NATIVE JSON MODEL & DATASET
# ==========================================
xgb_model = None
df = None

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(BASE_DIR, 'metroflow_xgboost_model.json')
dataset_path = os.path.join(BASE_DIR, 'AI_MetroFlow_Master_Dataset.xlsx')

try:
    if os.path.exists(model_path):
        xgb_model = xgb.XGBRegressor()
        xgb_model.load_model(model_path)
        print("Pre-trained XGBoost model successfully loaded via native JSON format!")
    else:
        print(f"Model file not found at {model_path}")
        
    if os.path.exists(dataset_path):
        df = pd.read_excel(dataset_path)
        print("Dataset successfully loaded into FastAPI backend!")
    else:
        print(f"Dataset file not found at {dataset_path}")
except Exception as e:
    print("Detailed Error loading model or dataset:")
    traceback.print_exc()
    xgb_model = None

# ==========================================
# 3. PYDANTIC REQUEST SCHEMAS
# ==========================================
class StationRequest(BaseModel):
    entry_hour: int = Field(..., ge=0, le=23, description="Hour of the day (0-23)")
    day_of_week: Optional[Union[int, str]] = Field(default=1, description="Day of week (0-6 or name e.g. Monday)")
    is_peak_hour: Optional[int] = Field(default=None, description="1 for peak rush hour, 0 for off-peak")
    hour_sin: Optional[float] = Field(default=None, description="Cyclical sine encoding of hour")
    hour_cos: Optional[float] = Field(default=None, description="Cyclical cosine encoding of hour")
    from_station: Optional[Union[int, str]] = Field(default=4, description="Station ID (0-4) or Station Name")
    to_station: Optional[Union[int, str]] = Field(default=2, description="Station ID (0-4) or Station Name")
    line_color: Optional[Union[int, str]] = Field(default=1, description="Line Color ID (0-3) or Line Name")
    train_capacity: int = Field(default=2400, description="Train capacity (1500, 1800, 2400)")

# ==========================================
# 4. HELPER FUNCTIONS
# ==========================================
def resolve_encoding(val: Union[int, str], mapping: dict, default_int: int = 0) -> int:
    if isinstance(val, int):
        return val
    if isinstance(val, str):
        if val in mapping:
            return mapping[val]
        try:
            return int(val)
        except ValueError:
            return default_int
    return default_int

def compute_cyclical_features(hour: int):
    hour_sin = float(np.sin(2 * np.pi * hour / 24.0))
    hour_cos = float(np.cos(2 * np.pi * hour / 24.0))
    is_peak = 1 if (8 <= hour <= 11) or (17 <= hour <= 20) else 0
    return hour_sin, hour_cos, is_peak

def trigger_overcrowding_alert(station_identifier: Any, hour: int, predicted_pax: float, capacity: int = 2400):
    """Automatically fires notification warnings when congestion exceeds safety limits."""
    occupancy_pct = round((predicted_pax / capacity) * 100, 1) if capacity > 0 else 0
    
    # Format station name if integer ID passed
    st_name = INV_STATION_MAPPING.get(station_identifier, str(station_identifier))
    
    if predicted_pax >= 1500:
        return {
            "alert_level": "CRITICAL_OVERCROWDING",
            "tier": "SEVERE_RUSH",
            "is_emergency": True,
            "occupancy_rate_pct": occupancy_pct,
            "message": f"🚨 Overcrowding Alert: {st_name} at {hour:02d}:00 is projected to reach {predicted_pax:.0f} passengers ({occupancy_pct}% capacity). High-frequency fleet dispatch activated.",
            "recommended_action": "Reduce headway to 3 minutes (High-Frequency Dispatch)",
            "channels_notified": ["Central Dispatch OCC", "Platform Digital Signage", "Mobile App Notifications", "PA Audio Broadcast"]
        }
    elif predicted_pax >= 800:
        return {
            "alert_level": "MODERATE_CONGESTION",
            "tier": "MODERATE_TRAFFIC",
            "is_emergency": False,
            "occupancy_rate_pct": occupancy_pct,
            "message": f"🟡 Moderate Traffic: {st_name} at {hour:02d}:00 projected at {predicted_pax:.0f} passengers ({occupancy_pct}% capacity). Standard schedule in effect.",
            "recommended_action": "Maintain standard headway (5-6 Minutes)",
            "channels_notified": ["Web Dashboard", "Station Manager Desk"]
        }
    else:
        return {
            "alert_level": "NORMAL",
            "tier": "OFF_PEAK",
            "is_emergency": False,
            "occupancy_rate_pct": occupancy_pct,
            "message": f"🟢 Off-Peak Flow: {st_name} at {hour:02d}:00 projected at {predicted_pax:.0f} passengers ({occupancy_pct}% capacity). Optimal passenger comfort.",
            "recommended_action": "Extend headway to 10 minutes (Conserve Fleet)",
            "channels_notified": ["Routine Log"]
        }

# ==========================================
# 5. FASTAPI ENDPOINTS
# ==========================================

@app.get("/")
def home():
    return {
        "platform": "MetroFlow AI Transit Intelligence Platform",
        "status": "Online",
        "architecture": "Production-Ready via Native XGBoost JSON IO",
        "model_loaded": xgb_model is not None,
        "dataset_loaded": df is not None
    }

@app.get("/api/meta")
def get_metadata():
    """Returns available stations, line colors, capacities, and days for UI dropdowns."""
    return {
        "stations": [
            {"id": 0, "name": "Botanical Garden", "line": "Magenta Line", "code": "BG"},
            {"id": 1, "name": "Dwarka Sec 21", "line": "Blue Line", "code": "DW21"},
            {"id": 2, "name": "Hauz Khas", "line": "Yellow / Magenta", "code": "HK"},
            {"id": 3, "name": "Kashmere Gate", "line": "Red / Yellow", "code": "KG"},
            {"id": 4, "name": "Rajiv Chowk", "line": "Blue / Yellow", "code": "RC"}
        ],
        "lines": [
            {"id": 0, "name": "Blue Line", "color": "#0284c7", "hex": "#0284c7"},
            {"id": 1, "name": "Magenta Line", "color": "#db2777", "hex": "#db2777"},
            {"id": 2, "name": "Red Line", "color": "#ef4444", "hex": "#ef4444"},
            {"id": 3, "name": "Yellow Line", "color": "#eab308", "hex": "#eab308"}
        ],
        "capacities": [1500, 1800, 2400],
        "days": [
            {"id": 0, "name": "Friday"},
            {"id": 1, "name": "Monday"},
            {"id": 2, "name": "Saturday"},
            {"id": 3, "name": "Sunday"},
            {"id": 4, "name": "Thursday"},
            {"id": 5, "name": "Tuesday"},
            {"id": 6, "name": "Wednesday"}
        ],
        "default_capacity": 2400,
        "critical_threshold": 1500,
        "moderate_threshold": 800
    }

@app.post("/api/predict")
def predict_occupancy(data: StationRequest):
    """AI Prediction Module: Predicts passenger count using the pre-trained XGBoost model."""
    if not xgb_model:
        raise HTTPException(status_code=500, detail="Pre-trained XGBoost model is not loaded.")
    
    # Resolve encodings
    from_st_id = resolve_encoding(data.from_station, STATION_MAPPING, default_int=4)
    to_st_id = resolve_encoding(data.to_station, STATION_MAPPING, default_int=2)
    line_id = resolve_encoding(data.line_color, LINE_MAPPING, default_int=1)
    
    # Resolve day of week
    if isinstance(data.day_of_week, str):
        day_id = DAY_MAPPING.get(data.day_of_week.capitalize(), 1)
    else:
        day_id = data.day_of_week
        
    # Auto-compute cyclical & peak features if not supplied
    auto_sin, auto_cos, auto_peak = compute_cyclical_features(data.entry_hour)
    hour_sin = data.hour_sin if data.hour_sin is not None else auto_sin
    hour_cos = data.hour_cos if data.hour_cos is not None else auto_cos
    is_peak = data.is_peak_hour if data.is_peak_hour is not None else auto_peak
    
    # Construct exact feature vector for XGBoost model
    input_dict = {
        'Entry_Hour': data.entry_hour,
        'Day_of_Week': day_id,
        'Is_Peak_Hour': is_peak,
        'Hour_Sin': hour_sin,
        'Hour_Cos': hour_cos,
        'From_Station': from_st_id,
        'To_Station': to_st_id,
        'Line_Color': line_id,
        'Train_Capacity': data.train_capacity
    }
    
    input_df = pd.DataFrame([input_dict])
    prediction = float(xgb_model.predict(input_df)[0])
    # Keep non-negative
    prediction = max(0.0, prediction)
    
    # Determine alert and schedule advisory
    alert_triggered = trigger_overcrowding_alert(from_st_id, data.entry_hour, prediction, data.train_capacity)
    
    # Recommended headway
    if prediction >= 1500:
        headway = 3
        action = "Reduce Headway to 3 Minutes (High-Frequency Dispatch)"
    elif prediction >= 800:
        headway = 6
        action = "Maintain Standard Headway (5-6 Minutes)"
    else:
        headway = 10
        action = "Extend Headway to 10 Minutes (Conserve Fleet)"
    
    return {
        "predicted_occupancy": round(prediction, 2),
        "predicted_occupancy_int": int(round(prediction)),
        "train_capacity": data.train_capacity,
        "occupancy_rate_pct": round((prediction / data.train_capacity) * 100, 1),
        "is_peak_hour": bool(is_peak),
        "from_station": INV_STATION_MAPPING.get(from_st_id, str(from_st_id)),
        "to_station": INV_STATION_MAPPING.get(to_st_id, str(to_st_id)),
        "line_color": INV_LINE_MAPPING.get(line_id, str(line_id)),
        "entry_hour_formatted": f"{data.entry_hour:02d}:00",
        "recommended_headway_min": headway,
        "fleet_action": action,
        "alert_status": alert_triggered
    }

@app.get("/api/schedule-advisory")
def get_schedule_advisory():
    """Scheduling Management Module: Generates network-wide traffic analysis and fleet directives."""
    if df is None:
        # Fallback simulated dataset if excel isn't present
        return {
            "total_records_analyzed": 0,
            "directives": [],
            "tier_counts": {"SEVERE_RUSH": 0, "MODERATE_TRAFFIC": 0, "OFF_PEAK": 0}
        }
    
    sample_data = df.tail(100).copy()
    sample_data['Entry_Hour'] = pd.to_datetime(sample_data['Exact_Entry_Timestamp']).dt.hour
    
    advisory_rows = []
    tier_counts = {"SEVERE_RUSH": 0, "MODERATE_TRAFFIC": 0, "OFF_PEAK": 0}
    
    for idx, row in sample_data.iterrows():
        station = str(row['From_Station'])
        dest = str(row['To_Station']) if 'To_Station' in row else "Network Hub"
        line = str(row['Line_Color']) if 'Line_Color' in row else "Metro Main"
        hour = int(row['Entry_Hour'])
        pax = float(row['Train_Occupancy_Count'])
        train_id = str(row.get('Train_ID', f"TR_{idx+1000}"))
        capacity = int(row.get('Train_Capacity', 2400))
        
        if pax >= 1500:
            tier = "SEVERE_RUSH"
            headway = 3
            action = "🔴 Reduce Headway to 3 Minutes (High-Frequency Dispatch)"
            status_label = "🔴 SEVERE RUSH HOUR"
        elif pax >= 800:
            tier = "MODERATE_TRAFFIC"
            headway = 6
            action = "🟡 Maintain Standard Headway (5-6 Minutes)"
            status_label = "🟡 MODERATE TRAFFIC"
        else:
            tier = "OFF_PEAK"
            headway = 10
            action = "🟢 Extend Headway to 10 Minutes (Conserve Fleet)"
            status_label = "🟢 OFF-PEAK"
            
        tier_counts[tier] = tier_counts.get(tier, 0) + 1
            
        advisory_rows.append({
            "trip_id": int(row.get('TripID', idx + 1)),
            "train_id": train_id,
            "station_id": station,
            "from_station": station,
            "to_station": dest,
            "line_color": line,
            "entry_hour": f"{hour:02d}:00",
            "hour_int": hour,
            "predicted_occupancy": round(pax, 2),
            "train_capacity": capacity,
            "occupancy_rate_pct": round((pax / capacity) * 100, 1),
            "traffic_tier": tier,
            "status_message": status_label,
            "recommended_headway_min": headway,
            "fleet_action": action
        })
        
    return {
        "total_records_analyzed": len(advisory_rows),
        "tier_counts": tier_counts,
        "directives": advisory_rows
    }

@app.get("/api/analytics")
def get_analytics():
    """Provides aggregated hourly occupancy statistics and station load distribution."""
    if df is None:
        raise HTTPException(status_code=500, detail="Master dataset not loaded.")
    
    analytics_df = df.copy()
    analytics_df['Entry_Hour'] = pd.to_datetime(analytics_df['Exact_Entry_Timestamp']).dt.hour
    
    # Hourly average crowd distribution
    hourly_avg = analytics_df.groupby('Entry_Hour')['Train_Occupancy_Count'].agg(
        avg_occupancy='mean',
        max_occupancy='max',
        min_occupancy='min',
        trip_count='count'
    ).reset_index()
    
    hourly_data = []
    for _, row in hourly_avg.iterrows():
        h = int(row['Entry_Hour'])
        avg_occ = round(float(row['avg_occupancy']), 1)
        is_rush = avg_occ >= 1500
        is_mod = 800 <= avg_occ < 1500
        hourly_data.append({
            "hour": h,
            "hour_label": f"{h:02d}:00",
            "avg_occupancy": avg_occ,
            "max_occupancy": round(float(row['max_occupancy']), 1),
            "min_occupancy": round(float(row['min_occupancy']), 1),
            "trip_count": int(row['trip_count']),
            "tier": "SEVERE_RUSH" if is_rush else ("MODERATE_TRAFFIC" if is_mod else "OFF_PEAK"),
            "is_rush_hour": (8 <= h <= 11) or (17 <= h <= 20)
        })
        
    # Station crowd breakdown
    station_avg = analytics_df.groupby('From_Station')['Train_Occupancy_Count'].agg(
        avg_occupancy='mean',
        total_trips='count'
    ).reset_index()
    
    station_data = []
    for _, row in station_avg.iterrows():
        station_data.append({
            "station": str(row['From_Station']),
            "avg_occupancy": round(float(row['avg_occupancy']), 1),
            "total_trips": int(row['total_trips'])
        })
        
    # Hourly station rankings breakdown
    hourly_station_breakdown = {}
    for h in sorted(analytics_df['Entry_Hour'].unique()):
        h_df = analytics_df[analytics_df['Entry_Hour'] == h]
        st_group = h_df.groupby('From_Station')['Train_Occupancy_Count'].agg(
            avg_occupancy='mean',
            total_trips='count'
        ).reset_index()
        station_ranks = []
        for _, s_row in st_group.iterrows():
            pax = round(float(s_row['avg_occupancy']), 1)
            station_ranks.append({
                "station": str(s_row['From_Station']),
                "avg_occupancy": pax,
                "total_trips": int(s_row['total_trips']),
                "tier": "SEVERE_RUSH" if pax >= 1500 else ("MODERATE_TRAFFIC" if pax >= 800 else "OFF_PEAK")
            })
        station_ranks.sort(key=lambda x: x['avg_occupancy'], reverse=True)
        hourly_station_breakdown[int(h)] = station_ranks

    # Line distribution
    line_avg = analytics_df.groupby('Line_Color')['Train_Occupancy_Count'].agg(
        avg_occupancy='mean',
        total_trips='count'
    ).reset_index()
    
    line_data = []
    for _, row in line_avg.iterrows():
        line_data.append({
            "line": str(row['Line_Color']),
            "avg_occupancy": round(float(row['avg_occupancy']), 1),
            "total_trips": int(row['total_trips'])
        })
        
    return {
        "total_trips": len(analytics_df),
        "overall_avg_occupancy": round(float(analytics_df['Train_Occupancy_Count'].mean()), 1),
        "peak_max_occupancy": int(analytics_df['Train_Occupancy_Count'].max()),
        "hourly_distribution": sorted(hourly_data, key=lambda x: x['hour']),
        "hourly_station_breakdown": hourly_station_breakdown,
        "station_distribution": sorted(station_data, key=lambda x: x['avg_occupancy'], reverse=True),
        "line_distribution": line_data,
        "critical_threshold": 1500,
        "moderate_threshold": 800
    }