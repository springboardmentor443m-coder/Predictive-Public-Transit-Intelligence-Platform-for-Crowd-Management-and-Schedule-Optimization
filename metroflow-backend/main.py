from fastapi import FastAPI, HTTPException, Depends, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Union, List, Dict, Any
import pandas as pd
import numpy as np
import xgboost as xgb
import traceback
import os
from pydantic import BaseModel, Field

# Auth & Database
from auth import (
    hash_password, verify_password, create_access_token, decode_token,
    authenticate_user, ensure_default_admin
)
from database import init_db, save_prediction, PredictionRecord, User, get_user_by_username, create_user

router = APIRouter()
security = HTTPBearer(auto_error=False)

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
# 0b. DATABASE INITIALIZATION & AUTH SETUP
# ==========================================
@app.on_event("startup")
async def startup():
    await init_db()
    await ensure_default_admin()


# ==========================================
# 0c. AUTH ROUTER
# ==========================================
class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    password: str
    role: str = "user"

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    username: str
    role: str
    message: str = ""

@router.post("/api/auth/login", response_model=LoginResponse)
async def login(data: LoginRequest):
    """Authenticate user and return JWT access token."""
    result = await authenticate_user(data.username, data.password)
    if not result:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return LoginResponse(
        access_token=result["access_token"],
        token_type=result["token_type"],
        username=result["username"],
        role=result["role"],
        message="Login successful!"
    )

@router.post("/api/auth/register")
async def register(data: RegisterRequest):
    """Register a new user."""
    existing = await get_user_by_username(data.username)
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    await create_user(data.username, hash_password(data.password), data.role)
    return {"message": f"User '{data.username}' registered successfully!"}

@router.get("/api/auth/me")
async def get_me(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user profile."""
    payload = decode_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = await get_user_by_username(payload.get("sub"))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "username": user.username,
        "role": user.role,
        "is_active": user.is_active
    }

app.include_router(router, prefix="")


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
async def predict_occupancy(data: StationRequest):
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
        recommended_rake_cap = 2400
        recommended_rake_formation = "8-Coach (2,400 pax) High-Capacity Heavy Metro Rake"
        recommended_rake_desc = "High-density crowd requires maximum 8-coach rake formation to prevent platform overcrowding and maintain safety margins."
    elif prediction >= 800:
        headway = 6
        action = "Maintain Standard Headway (5-6 Minutes)"
        recommended_rake_cap = 1800
        recommended_rake_formation = "6-Coach (1,800 pax) Standard Mainline Rake"
        recommended_rake_desc = "Standard 6-coach mainline rake provides optimal passenger comfort and energy efficiency for moderate flow."
    else:
        headway = 10
        action = "Extend Headway to 10 Minutes (Conserve Fleet)"
        recommended_rake_cap = 1500
        recommended_rake_formation = "4-Coach (1,500 pax) Standard Feeder Rake"
        recommended_rake_desc = "4-coach feeder rake formation is optimal for off-peak passenger volume, minimizing idle coach power and fleet wear."
    
    # Save prediction to database
    day_name = DAY_INDEX_TO_NAME[day_id] if isinstance(day_id, int) and 0 <= day_id < len(DAY_INDEX_TO_NAME) else "Monday"
    prediction_record = PredictionRecord(
        from_station=INV_STATION_MAPPING.get(from_st_id, str(from_st_id)),
        to_station=INV_STATION_MAPPING.get(to_st_id, str(to_st_id)),
        line_color=INV_LINE_MAPPING.get(line_id, str(line_id)),
        entry_hour=data.entry_hour,
        day_of_week=day_name,
        train_capacity=data.train_capacity,
        predicted_occupancy=round(prediction, 2),
        occupancy_rate_pct=round((prediction / data.train_capacity) * 100, 1),
        recommended_headway=headway,
        traffic_tier=alert_triggered.get('tier', 'OFF_PEAK'),
        fleet_action=action,
        alert_level=alert_triggered.get('alert_level', 'NORMAL')
    )
    await save_prediction(prediction_record)

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
        "recommended_rake_capacity": recommended_rake_cap,
        "recommended_rake_formation": recommended_rake_formation,
        "recommended_rake_desc": recommended_rake_desc,
        "fleet_action": action,
        "alert_status": alert_triggered
    }

@app.get("/api/schedule-advisory")
def get_schedule_advisory(
    from_station: Optional[str] = None,
    to_station: Optional[str] = None,
    line: Optional[str] = None,
    hour: Optional[int] = None
):
    """Scheduling Management Module: Generates fleet directives based on prediction or dataset."""
    if df is None:
        return {
            "total_records_analyzed": 0,
            "directives": [],
            "tier_counts": {"SEVERE_RUSH": 0, "MODERATE_TRAFFIC": 0, "OFF_PEAK": 0},
            "prediction_based": False
        }
    
    sample_data = df.tail(100).copy()
    sample_data['Entry_Hour'] = pd.to_datetime(sample_data['Exact_Entry_Timestamp']).dt.hour
    
    # Filter by prediction parameters if provided
    if from_station is not None:
        sample_data = sample_data[sample_data['From_Station'].astype(str) == str(from_station)]
    if to_station is not None:
        sample_data = sample_data[sample_data['To_Station'].astype(str) == str(to_station)]
    if line is not None:
        sample_data = sample_data[sample_data['Line_Color'].astype(str) == str(line)]
    if hour is not None:
        sample_data = sample_data[sample_data['Entry_Hour'] == hour]
    
    # If no matching rows, fall back to all data
    if len(sample_data) == 0:
        sample_data = df.tail(100).copy()
        sample_data['Entry_Hour'] = pd.to_datetime(sample_data['Exact_Entry_Timestamp']).dt.hour
    
    advisory_rows = []
    tier_counts = {"SEVERE_RUSH": 0, "MODERATE_TRAFFIC": 0, "OFF_PEAK": 0}
    
    for idx, row in sample_data.iterrows():
        station = str(row['From_Station'])
        dest = str(row['To_Station']) if 'To_Station' in row else "Network Hub"
        line_color = str(row['Line_Color']) if 'Line_Color' in row else "Metro Main"
        hr = int(row['Entry_Hour'])
        pax = float(row['Train_Occupancy_Count'])
        train_id = str(row.get('Train_ID', f"TR_{idx+1000}"))
        capacity = int(row.get('Train_Capacity', 2400))
        
        if pax >= 1500:
            tier = "SEVERE_RUSH"
            hw = 3
            action = "🔴 Reduce Headway to 3 Minutes (High-Frequency Dispatch)"
            status_label = "🔴 SEVERE RUSH HOUR"
        elif pax >= 800:
            tier = "MODERATE_TRAFFIC"
            hw = 6
            action = "🟡 Maintain Standard Headway (5-6 Minutes)"
            status_label = "🟡 MODERATE TRAFFIC"
        else:
            tier = "OFF_PEAK"
            hw = 10
            action = "🟢 Extend Headway to 10 Minutes (Conserve Fleet)"
            status_label = "🟢 OFF-PEAK"
            
        tier_counts[tier] = tier_counts.get(tier, 0) + 1
            
        advisory_rows.append({
            "trip_id": int(row.get('TripID', idx + 1)),
            "train_id": train_id,
            "station_id": station,
            "from_station": station,
            "to_station": dest,
            "line_color": line_color,
            "entry_hour": f"{hr:02d}:00",
            "hour_int": hr,
            "predicted_occupancy": round(pax, 2),
            "train_capacity": capacity,
            "occupancy_rate_pct": round((pax / capacity) * 100, 1),
            "traffic_tier": tier,
            "status_message": status_label,
            "recommended_headway_min": hw,
            "fleet_action": action
        })
        
    return {
        "total_records_analyzed": len(advisory_rows),
        "tier_counts": tier_counts,
        "prediction_based": from_station is not None or to_station is not None or line is not None or hour is not None,
        "filter": {"from_station": from_station, "to_station": to_station, "line": line, "hour": hour},
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
        
    # Hourly station rankings breakdown with operating Train IDs
    hourly_station_breakdown = {}
    for h in sorted(analytics_df['Entry_Hour'].unique()):
        h_df = analytics_df[analytics_df['Entry_Hour'] == h]
        st_group = h_df.groupby('From_Station')
        station_ranks = []
        for station_name, group in st_group:
            pax = round(float(group['Train_Occupancy_Count'].mean()), 1)
            train_ids = [str(tid) for tid in group['Train_ID'].dropna().unique()[:4]]
            lines = [str(l) for l in group['Line_Color'].dropna().unique()[:2]]
            tier = "SEVERE_RUSH" if pax >= 1500 else ("MODERATE_TRAFFIC" if pax >= 800 else "OFF_PEAK")
            headway = 3 if pax >= 1500 else (6 if pax >= 800 else 10)
            
            station_ranks.append({
                "station": str(station_name),
                "avg_occupancy": pax,
                "total_trips": int(len(group)),
                "train_ids": train_ids if train_ids else [f"TR_{int(h)*100+1}", f"TR_{int(h)*100+2}"],
                "lines": lines if lines else ["Metro Main"],
                "tier": tier,
                "recommended_headway": headway
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

@app.get("/api/alerts")
def get_alerts_and_notifications():
    """Alert & Notification Module: Real-time feed of Overcrowding Alerts, Delay Notifications, and Emergency Announcements."""
    overcrowding_list = []
    delay_list = []
    
    if df is not None:
        # Sample recent records for live alerts
        recent_df = df.tail(80).copy()
        recent_df['Entry_Hour'] = pd.to_datetime(recent_df['Exact_Entry_Timestamp']).dt.hour
        
        # 1. Overcrowding Alerts (Occupancy >= 1400)
        overcrowded = recent_df[recent_df['Train_Occupancy_Count'] >= 1400].head(8)
        for idx, row in overcrowded.iterrows():
            pax = int(round(float(row['Train_Occupancy_Count'])))
            cap = int(row.get('Train_Capacity', 2400))
            pct = round((pax / cap) * 100, 1)
            st = str(row['From_Station'])
            line = str(row.get('Line_Color', 'Yellow Line'))
            tid = str(row.get('Train_ID', f"TR_{idx+1000}"))
            hr = int(row['Entry_Hour'])
            is_crit = pax >= 1500
            
            overcrowding_list.append({
                "id": f"OC-{idx+100}",
                "type": "OVERCROWDING",
                "station": st,
                "line": line,
                "train_id": tid,
                "hour_formatted": f"{hr:02d}:00",
                "occupancy": pax,
                "capacity": cap,
                "occupancy_rate_pct": pct,
                "severity": "CRITICAL" if is_crit else "WARNING",
                "title": f"🚨 Severe Platform Congestion at {st}" if is_crit else f"🟡 Heavy Influx Detected at {st}",
                "message": f"Projected {pax:,} passengers ({pct}% capacity). Platform density exceeds safety limits." if is_crit else f"Passenger density reaching {pax:,} pax ({pct}%). Standby fleet alert active.",
                "recommended_action": "Activate 3-Minute Rapid Headway Dispatch & 8-Coach Rake" if is_crit else "Maintain 5-6 Minute Regular Headway",
                "channels_notified": ["Central Dispatch OCC", "Platform Digital Signage", "Mobile App Notifications", "PA Audio Broadcast"],
                "timestamp": "Just now"
            })
            
        # 2. Delay Notifications (Historical / Computed Delay > 2 min)
        delay_col = 'Historical Delay (min)' if 'Historical Delay (min)' in recent_df.columns else None
        if delay_col:
            delayed = recent_df[recent_df[delay_col] >= 3].head(8)
            reasons = [
                "Heavy passenger boarding & platform dwell time overrun",
                "Headway compression regulation for crowd clearance",
                "Interchange track junction speed restriction",
                "Platform door clearance cycle extended by rush influx"
            ]
            for idx, row in delayed.iterrows():
                delay_val = int(row[delay_col])
                st = str(row['From_Station'])
                dest = str(row.get('To_Station', 'Network Hub'))
                line = str(row.get('Line_Color', 'Yellow Line'))
                tid = str(row.get('Train_ID', f"TR_{idx+2000}"))
                hr = int(row['Entry_Hour'])
                reason = reasons[idx % len(reasons)]
                
                delay_list.append({
                    "id": f"DL-{idx+200}",
                    "type": "DELAY",
                    "train_id": tid,
                    "line": line,
                    "from_station": st,
                    "to_station": dest,
                    "scheduled_time": f"{hr:02d}:15",
                    "revised_time": f"{hr:02d}:{15 + delay_val:02d}",
                    "delay_minutes": delay_val,
                    "severity": "HIGH_DELAY" if delay_val >= 7 else "MODERATE_DELAY",
                    "title": f"⏱️ Train {tid} Delayed (+{delay_val} min)",
                    "message": f"{line} Train {tid} bound for {dest} running {delay_val} minutes behind schedule at {st}.",
                    "cause": reason,
                    "resolution": "Automated speed envelope adjustment & prioritized green wave signal dispatch",
                    "channels_notified": ["Passenger Digital Displays", "Mobile Trip Planner", "OCC Track Controller"],
                    "timestamp": f"{delay_val + 1}m ago"
                })

    # Fallbacks if dataset yields fewer rows
    if len(overcrowding_list) == 0:
        overcrowding_list = [
            {
                "id": "OC-101",
                "type": "OVERCROWDING",
                "station": "Rajiv Chowk",
                "line": "Yellow Line",
                "train_id": "TR_7977",
                "hour_formatted": "18:00",
                "occupancy": 1850,
                "capacity": 2400,
                "occupancy_rate_pct": 77.1,
                "severity": "CRITICAL",
                "title": "🚨 Severe Platform Congestion at Rajiv Chowk",
                "message": "Projected 1,850 passengers (77.1% capacity). High platform density detected during evening rush hour.",
                "recommended_action": "Activate 3-Minute Rapid Headway Dispatch & 8-Coach Rake",
                "channels_notified": ["Central Dispatch OCC", "Platform Digital Signage", "Mobile App Notifications", "PA Audio Broadcast"],
                "timestamp": "Just now"
            },
            {
                "id": "OC-102",
                "type": "OVERCROWDING",
                "station": "Kashmere Gate",
                "line": "Red Line",
                "train_id": "TR_9528",
                "hour_formatted": "09:00",
                "occupancy": 1720,
                "capacity": 2400,
                "occupancy_rate_pct": 71.7,
                "severity": "CRITICAL",
                "title": "🚨 Platform Overcrowding Warning at Kashmere Gate",
                "message": "Projected 1,720 passengers. North corridor interchange influx exceeding nominal safety threshold.",
                "recommended_action": "Deploy empty feeder train from depot to Kashmere Gate platform 2",
                "channels_notified": ["Central Dispatch OCC", "Platform Digital Signage", "Mobile App Notifications"],
                "timestamp": "2m ago"
            },
            {
                "id": "OC-103",
                "type": "OVERCROWDING",
                "station": "Hauz Khas",
                "line": "Magenta Line",
                "train_id": "TR_4144",
                "hour_formatted": "18:00",
                "occupancy": 1420,
                "capacity": 1800,
                "occupancy_rate_pct": 78.9,
                "severity": "WARNING",
                "title": "🟡 Elevated Passenger Density at Hauz Khas",
                "message": "Projected 1,420 passengers. Tech corridor evening transfer volume rising.",
                "recommended_action": "Maintain 5-Minute Mainline Dispatch",
                "channels_notified": ["Station Manager Desk", "Platform Displays"],
                "timestamp": "5m ago"
            }
        ]

    if len(delay_list) == 0:
        delay_list = [
            {
                "id": "DL-201",
                "type": "DELAY",
                "train_id": "TR_1412",
                "line": "Blue Line",
                "from_station": "Botanical Garden",
                "to_station": "Dwarka Sec 21",
                "scheduled_time": "18:15",
                "revised_time": "18:21",
                "delay_minutes": 6,
                "severity": "MODERATE_DELAY",
                "title": "⏱️ Train TR_1412 Delayed (+6 min)",
                "message": "Blue Line Train TR_1412 running 6 minutes behind schedule departing Botanical Garden.",
                "cause": "Platform dwell time extended by high passenger boarding volume at Noida sector interchanges",
                "resolution": "Extended dwell time compensation applied at Rajiv Chowk bypass",
                "channels_notified": ["Passenger Digital Displays", "Mobile Trip Planner", "OCC Desk"],
                "timestamp": "3m ago"
            },
            {
                "id": "DL-202",
                "type": "DELAY",
                "train_id": "TR_8506",
                "line": "Yellow Line",
                "from_station": "Kashmere Gate",
                "to_station": "Hauz Khas",
                "scheduled_time": "09:10",
                "revised_time": "09:18",
                "delay_minutes": 8,
                "severity": "HIGH_DELAY",
                "title": "⏱️ Train TR_8506 Delayed (+8 min)",
                "message": "Yellow Line Train TR_8506 delayed 8 minutes due to track signal regulation.",
                "cause": "Speed restriction enforced to maintain safe 3-minute braking separation behind TR_9528",
                "resolution": "Signal green-wave clearance active through Central Secretariat junction",
                "channels_notified": ["Platform Signage", "OCC Track Control", "Mobile App Notifications"],
                "timestamp": "7m ago"
            }
        ]

    # 3. Emergency Announcements (OCC Broadcast Live Feed)
    emergency_announcements = [
        {
            "id": "EM-301",
            "type": "EMERGENCY_ANNOUNCEMENT",
            "priority": "URGENT",
            "broadcast_system": "PA Audio & Digital VMS Signage",
            "title": "📢 OCC Broadcast: Platform Clearance Directive - Rajiv Chowk",
            "station_scope": "Rajiv Chowk (Platform 1 & 2)",
            "message": "Attention passengers at Rajiv Chowk: Please stand clear of platform screen doors. High-frequency 8-coach train arriving in 90 seconds. Do not rush the boarding area.",
            "audio_chime": "Standard 3-Tone Alert Chime",
            "target_channels": ["Platform PA Audio Speakers", "Overhead LED Display Signage", "Metro Mobile App Push", "OCC Wall Monitor"],
            "status": "BROADCASTING_ACTIVE",
            "timestamp": "Live Active"
        },
        {
            "id": "EM-302",
            "type": "EMERGENCY_ANNOUNCEMENT",
            "priority": "HIGH",
            "broadcast_system": "Mobile App & Digital Signage",
            "title": "📢 Crowd Regulation Notice: Kashmere Gate Multi-Line Transfer",
            "station_scope": "Kashmere Gate (Red / Yellow Interchange)",
            "message": "Passenger flow regulation in effect at Kashmere Gate escalators. Yellow Line trains departing every 3 minutes. Follow station marshal instructions for seamless transfer.",
            "audio_chime": "Advisory Dual-Tone Chime",
            "target_channels": ["Interchange Concourse Displays", "Station PA System", "Customer Service Desk"],
            "status": "SCHEDULED_REPEATING",
            "timestamp": "Every 2 Minutes"
        },
        {
            "id": "EM-303",
            "type": "EMERGENCY_ANNOUNCEMENT",
            "priority": "ADVISORY",
            "broadcast_system": "Network-Wide OCC Broadcast",
            "title": "📢 Automated Fleet Directive: 3-Minute Headway Window Active",
            "station_scope": "Network-Wide (All 5 Master Hubs)",
            "message": "Central OCC automated dispatch has compressed headway to 3 minutes across Yellow and Blue lines to clear peak rush bottlenecks. Additional rake formations deployed.",
            "audio_chime": "Information Single Chime",
            "target_channels": ["OCC Operations Dashboard", "Train Operator Cabin Radio", "Station Master Terminals"],
            "status": "TRANSMITTING",
            "timestamp": "Updated 1m ago"
        }
    ]

    return {
        "status": "Success",
        "summary": {
            "total_active_alerts": len(overcrowding_list) + len(delay_list) + len(emergency_announcements),
            "overcrowding_count": len(overcrowding_list),
            "delay_count": len(delay_list),
            "emergency_announcements_count": len(emergency_announcements),
            "occ_broadcast_status": "Online & Broadcasting"
        },
        "overcrowding_alerts": overcrowding_list,
        "delay_notifications": delay_list,
        "emergency_announcements": emergency_announcements
    }