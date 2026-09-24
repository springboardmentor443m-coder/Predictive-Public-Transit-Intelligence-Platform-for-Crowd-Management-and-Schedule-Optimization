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
    authenticate_user, ensure_default_admin, get_user_by_username, create_user
)
from database import init_db, save_prediction, PredictionRecord, User

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
    from database import async_session
    async with async_session() as session:
        await ensure_default_admin(session)

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
    from auth import authenticate_user
    from database import async_session
    async with async_session() as session:
        result = await authenticate_user(data.username, data.password, session)
        if not result:
            raise HTTPException(status_code=401, detail="Invalid username or password")
        return LoginResponse(
            access_token=result["access_token"],
            token_type="bearer",
            username=result["username"],
            role=result["role"],
            message="Login successful!"
        )

@router.post("/api/auth/register")
async def register(data: RegisterRequest):
    """Register a new user."""
    from database import async_session, get_user_by_username, create_user as db_create_user
    existing = await get_user_by_username(data.username)
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    async with async_session() as session:
        await db_create_user(data.username, hash_password(data.password), data.role, session)
    return {"message": f"User '{data.username}' registered successfully!"}

@router.get("/api/auth/me")
async def get_me(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user profile."""
    payload = decode_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = await db_get_user(payload.get("sub"))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"username": user.username, "role": user.role, "is_active": user.is_active}

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
    'Friday': 0, 'Monday': 1, 'Saturday': 2, 'Sunday': 3,
    'Thursday': 4, 'Tuesday': 5, 'Wednesday': 6
}
INV_DAY_MAPPING = {v: k for k, v in DAY_MAPPING.items()}
DAY_INDEX_TO_NAME = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

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
    day_of_week: Optional[Union[int, str]] = Field(default=1, description="Day of week (0-6 or name)")
    is_peak_hour: Optional[int] = Field(default=None, description="1 for peak, 0 for off-peak")
    hour_sin: Optional[float] = Field(default=None)
    hour_cos: Optional[float] = Field(default=None)
    from_station: Optional[Union[int, str]] = Field(default=4, description="Station ID or Name")
    to_station: Optional[Union[int, str]] = Field(default=2, description="Station ID or Name")
    line_color: Optional[Union[int, str]] = Field(default=1, description="Line ID or Name")
    train_capacity: int = Field(default=2400, description="Train capacity")

# ==========================================
# 4. HELPER FUNCTIONS
# ==========================================
def resolve_encoding(val: Union[int, str], mapping: dict, default_int: int = 0) -> int:
    if isinstance(val, int): return val
    if isinstance(val, str):
        if val in mapping: return mapping[val]
        try: return int(val)
        except ValueError: return default_int
    return default_int

def compute_cyclical_features(hour: int):
    hour_sin = float(np.sin(2 * np.pi * hour / 24.0))
    hour_cos = float(np.cos(2 * np.pi * hour / 24.0))
    is_peak = 1 if (8 <= hour <= 11) or (17 <= hour <= 20) else 0
    return hour_sin, hour_cos, is_peak

def trigger_overcrowding_alert(station_identifier: Any, hour: int, predicted_pax: float, capacity: int = 2400):
    occupancy_pct = round((predicted_pax / capacity) * 100, 1) if capacity > 0 else 0
    st_name = INV_STATION_MAPPING.get(station_identifier, str(station_identifier))
    if predicted_pax >= 1500:
        return {"alert_level": "CRITICAL_OVERCROWDING", "tier": "SEVERE_RUSH", "is_emergency": True,
                "occupancy_rate_pct": occupancy_pct,
                "message": f"🚨 Overcrowding Alert: {st_name} at {hour:02d}:00 is projected to reach {predicted_pax:.0f} passengers ({occupancy_pct}% capacity). High-frequency fleet dispatch activated.",
                "recommended_action": "Reduce headway to 3 minutes (High-Frequency Dispatch)",
                "channels_notified": ["Central Dispatch OCC", "Platform Digital Signage", "Mobile App Notifications", "PA Audio Broadcast"]}
    elif predicted_pax >= 800:
        return {"alert_level": "MODERATE_CONGESTION", "tier": "MODERATE_TRAFFIC", "is_emergency": False,
                "occupancy_rate_pct": occupancy_pct,
                "message": f"🟡 Moderate Traffic: {st_name} at {hour:02d}:00 projected at {predicted_pax:.0f} passengers ({occupancy_pct}% capacity). Standard schedule in effect.",
                "recommended_action": "Maintain standard headway (5-6 Minutes)",
                "channels_notified": ["Web Dashboard", "Station Manager Desk"]}
    else:
        return {"alert_level": "NORMAL", "tier": "OFF_PEAK", "is_emergency": False,
                "occupancy_rate_pct": occupancy_pct,
                "message": f"🟢 Off-Peak Flow: {st_name} at {hour:02d}:00 projected at {predicted_pax:.0f} passengers ({occupancy_pct}% capacity). Optimal passenger comfort.",
                "recommended_action": "Extend headway to 10 minutes (Conserve Fleet)",
                "channels_notified": ["Routine Log"]}

# ==========================================
# 5. FASTAPI ENDPOINTS
# ==========================================
@app.get("/")
def home():
    return {"platform": "MetroFlow AI Transit Intelligence Platform", "status": "Online",
            "architecture": "Production-Ready via Native XGBoost JSON IO",
            "model_loaded": xgb_model is not None, "dataset_loaded": df is not None}

@app.get("/health")
def health():
    return {"status": "healthy", "database": "connected", "model_loaded": xgb_model is not None}

@app.get("/api/meta")
def get_metadata():
    return {"stations": [
        {"id": 0, "name": "Botanical Garden", "line": "Magenta Line", "code": "BG"},
        {"id": 1, "name": "Dwarka Sec 21", "line": "Blue Line", "code": "DW21"},
        {"id": 2, "name": "Hauz Khas", "line": "Yellow / Magenta", "code": "HK"},
        {"id": 3, "name": "Kashmere Gate", "line": "Red / Yellow", "code": "KG"},
        {"id": 4, "name": "Rajiv Chowk", "line": "Blue / Yellow", "code": "RC"}
    ], "lines": [
        {"id": 0, "name": "Blue Line", "color": "#0284c7", "hex": "#0284c7"},
        {"id": 1, "name": "Magenta Line", "color": "#db2777", "hex": "#db2777"},
        {"id": 2, "name": "Red Line", "color": "#ef4444", "hex": "#ef4444"},
        {"id": 3, "name": "Yellow Line", "color": "#eab308", "hex": "#eab308"}
    ], "capacities": [1500, 1800, 2400],
    "days": [{"id": i, "name": d} for i, d in enumerate(DAY_INDEX_TO_NAME)],
    "default_capacity": 2400, "critical_threshold": 1500, "moderate_threshold": 800}

@app.post("/api/predict")
async def predict_occupancy(data: StationRequest):
    """AI Prediction Module: Predicts passenger count using the pre-trained XGBoost model."""
    if not xgb_model:
        raise HTTPException(status_code=500, detail="Pre-trained XGBoost model is not loaded.")
    
    from_st_id = resolve_encoding(data.from_station, STATION_MAPPING, default_int=4)
    to_st_id = resolve_encoding(data.to_station, STATION_MAPPING, default_int=2)
    line_id = resolve_encoding(data.line_color, LINE_MAPPING, default_int=1)
    
    if isinstance(data.day_of_week, str):
        day_id = DAY_MAPPING.get(data.day_of_week.capitalize(), 1)
    else:
        day_id = data.day_of_week
        
    auto_sin, auto_cos, auto_peak = compute_cyclical_features(data.entry_hour)
    hour_sin = data.hour_sin if data.hour_sin is not None else auto_sin
    hour_cos = data.hour_cos if data.hour_cos is not None else auto_cos
    is_peak = data.is_peak_hour if data.is_peak_hour is not None else auto_peak
    
    input_dict = {'Entry_Hour': data.entry_hour, 'Day_of_Week': day_id, 'Is_Peak_Hour': is_peak,
                  'Hour_Sin': hour_sin, 'Hour_Cos': hour_cos, 'From_Station': from_st_id,
                  'To_Station': to_st_id, 'Line_Color': line_id, 'Train_Capacity': data.train_capacity}
    input_df = pd.DataFrame([input_dict])
    prediction = float(xgb_model.predict(input_df)[0])
    prediction = max(0.0, prediction)
    
    alert_triggered = trigger_overcrowding_alert(from_st_id, data.entry_hour, prediction, data.train_capacity)
    
    if prediction >= 1500:
        headway = 3
        action = "Reduce Headway to 3 Minutes (High-Frequency Dispatch)"
        rake_cap = 2400
        rake_formation = "8-Coach (2,400 pax) High-Capacity Heavy Metro Rake"
        rake_desc = "High-density crowd requires maximum 8-coach rake formation."
    elif prediction >= 800:
        headway = 6
        action = "Maintain Standard Headway (5-6 Minutes)"
        rake_cap = 1800
        rake_formation = "6-Coach (1,800 pax) Standard Mainline Rake"
        rake_desc = "Standard 6-coach mainline rake provides optimal passenger comfort."
    else:
        headway = 10
        action = "Extend Headway to 10 Minutes (Conserve Fleet)"
        rake_cap = 1500
        rake_formation = "4-Coach (1,500 pax) Standard Feeder Rake"
        rake_desc = "4-coach feeder rake formation is optimal for off-peak passenger volume."
    
    # Save prediction to database
    day_name = DAY_INDEX_TO_NAME[day_id] if isinstance(day_id, int) else "Monday"
    prediction_record = PredictionRecord(
        from_station=INV_STATION_MAPPING.get(from_st_id, str(from_st_id)),
        to_station=INV_STATION_MAPPING.get(to_st_id, str(to_st_id)),
        line_color=INV_LINE_MAPPING.get(line_id, str(line_id)),
        entry_hour=data.entry_hour,
        day_of_week=day_name,
        train_capacity=data.train_capacity,
        predicted_occupancy=round(prediction, 2),
        occupancy_rate_pct=round((prediction / data.train_capacity) * 100, 1),
        recommended_headway_min=headway,
        traffic_tier=alert_triggered["tier"],
        fleet_action=action,
        alert_level=alert_triggered["alert_level"]
    )
    from database import save_prediction
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
        "fleet_action": action,
        "alert_status": alert_triggered,
        "recommended_rake_capacity": rake_cap,
        "recommended_rake_formation": rake_formation,
        "recommended_rake_desc": rake_desc
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
        return {"total_records_analyzed": 0, "directives": [], "tier_counts": {}, "prediction_based": False}
    
    sample_data = df.tail(100).copy()
    sample_data['Entry_Hour'] = pd.to_datetime(sample_data['Exact_Entry_Timestamp']).dt.hour
    
    # Filter by prediction parameters if provided
    if from_station:
        sample_data = sample_data[sample_data['From_Station'].astype(str) == str(from_station)]
    if to_station:
        sample_data = sample_data[sample_data['To_Station'].astype(str) == str(to_station)]
    if line:
        sample_data = sample_data[sample_data['Line_Color'].astype(str) == str(line)]
    if hour:
        sample_data = sample_data[sample_data['Entry_Hour'] == hour]
    
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
            tier = "SEVERE_RUSH"; hw = 3
            action = "🔴 Reduce Headway to 3 Minutes (High-Frequency Dispatch)"
            status_label = "🔴 SEVERE RUSH HOUR"
        elif pax >= 800:
            tier = "MODERATE_TRAFFIC"; hw = 6
            action = "🟡 Maintain Standard Headway (5-6 Minutes)"
            status_label = "🟡 MODERATE TRAFFIC"
        else:
            tier = "OFF_PEAK"; hw = 10
            action = "🟢 Extend Headway to 10 Minutes (Conserve Fleet)"
            status_label = "🟢 OFF-PEAK"
        
        tier_counts[tier] = tier_counts.get(tier, 0) + 1
        advisory_rows.append({
            "trip_id": int(row.get('TripID', idx + 1)), "train_id": train_id,
            "station_id": station, "from_station": station, "to_station": dest,
            "line_color": line_color, "entry_hour": f"{hr:02d}:00", "hour_int": hr,
            "predicted_occupancy": round(pax, 2), "train_capacity": capacity,
            "occupancy_rate_pct": round((pax / capacity) * 100, 1),
            "traffic_tier": tier, "status_message": status_label,
            "recommended_headway_min": hw, "fleet_action": action
        })
    
    return {
        "total_records_analyzed": len(advisory_rows), "tier_counts": tier_counts,
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
    
    hourly_avg = analytics_df.groupby('Entry_Hour')['Train_Occupancy_Count'].agg(
        avg_occupancy='mean', max_occupancy='max', min_occupancy='min', trip_count='count'
    ).reset_index()
    
    hourly_data = []
    for _, row in hourly_avg.iterrows():
        h = int(row['Entry_Hour'])
        avg_occ = round(float(row['avg_occupancy']), 1)
        hourly_data.append({"hour": h, "hour_label": f"{h:02d}:00", "avg_occupancy": avg_occ,
                            "max_occupancy": round(float(row['max_occupancy']), 1),
                            "min_occupancy": round(float(row['min_occupancy']), 1),
                            "trip_count": int(row['trip_count']),
                            "tier": "SEVERE_RUSH" if avg_occ >= 1500 else ("MODERATE_TRAFFIC" if avg_occ >= 800 else "OFF_PEAK"),
                            "is_rush_hour": (8 <= h <= 11) or (17 <= h <= 20)})
    
    station_avg = analytics_df.groupby('From_Station')['Train_Occupancy_Count'].agg(
        avg_occupancy='mean', total_trips='count'
    ).reset_index()
    station_data = [{"station": str(r['From_Station']), "avg_occupancy": round(float(r['avg_occupancy']), 1), "total_trips": int(r['total_trips'])} for _, r in station_avg.iterrows()]
    
    return {"total_trips": len(analytics_df), "overall_avg_occupancy": round(float(analytics_df['Train_Occupancy_Count'].mean()), 1),
            "peak_max_occupancy": int(analytics_df['Train_Occupancy_Count'].max()),
            "hourly_distribution": sorted(hourly_data, key=lambda x: x['hour']),
            "station_distribution": sorted(station_data, key=lambda x: x['avg_occupancy'], reverse=True),
            "critical_threshold": 1500, "moderate_threshold": 800}

# ==========================================
# 6. PREDICTION HISTORY (REMOVED per mentor)
# ==========================================
# /api/auth/history and /api/auth/stats endpoints removed per mentor's requirement
# Predictions are still saved to database via save_prediction() but not exposed via API

