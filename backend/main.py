import json
import hashlib
import hmac
import os
import re
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional

import joblib
import jwt
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from pymongo import ASCENDING, MongoClient
from pymongo.errors import DuplicateKeyError
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODEL_FILE = PROJECT_ROOT / "backend" / "models" / "metroflow_demand_model.joblib"
DATA_FILE = PROJECT_ROOT / "data" / "metroflow_processed_network.csv"
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "metroflow")
JWT_SECRET = os.getenv("METROFLOW_JWT_SECRET", "development-only-change-this-secret")
JWT_EXPIRY_HOURS = int(os.getenv("METROFLOW_JWT_EXPIRY_HOURS", "8"))

app = FastAPI(
    title="MetroFlow Transit Intelligence Platform",
    description="Multi-station passenger flow forecasting, congestion tracking, and AI schedule optimization.",
    version="2.0.0",
)

allowed_origins = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in allowed_origins.split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory artifact store
ai_model_store = {
    "weights": None,
    "feature_cols": [],
    "metrics": {},
    "network_df": None,
}
mongo_client = None
auth_users_collection = None
operations_collection = None
auth_scheme = HTTPBearer(auto_error=False)


@app.on_event("startup")
def load_artifacts():
    initialize_auth_db()

    if MODEL_FILE.exists():
        artifact = joblib.load(MODEL_FILE)
        ai_model_store["weights"] = np.array(artifact["weights"])
        ai_model_store["feature_cols"] = artifact["feature_cols"]
        ai_model_store["metrics"] = artifact.get("metrics", {})

    if DATA_FILE.exists():
        ai_model_store["network_df"] = pd.read_csv(DATA_FILE)


# Pydantic Schemas
class PredictionRequest(BaseModel):
    station_code: int = Field(default=150, description="Station identifier")
    hour: int = Field(ge=0, le=23, description="Hour of the day (0-23)")
    day_of_week: int = Field(ge=0, le=6, description="0=Monday, 6=Sunday")
    is_weekend: int = Field(default=0, ge=0, le=1)
    is_peak_hour: int = Field(default=0, ge=0, le=1)
    lag_1h: float = Field(default=800.0, description="Passenger count 1 hour ago")
    lag_2h: float = Field(default=750.0, description="Passenger count 2 hours ago")
    rolling_3h: float = Field(default=780.0, description="Rolling 3-hour mean passenger demand")
    station_capacity: Optional[int] = Field(default=2500, description="Station nominal capacity")


class PredictionResponse(BaseModel):
    station_code: int
    predicted_passenger_demand: int
    occupancy_rate: float
    crowd_level: str
    metrics: Dict[str, float]


class ScheduleRecommendationRequest(BaseModel):
    station_code: int = 150
    predicted_demand: int
    station_capacity: int = 2500
    current_headway_minutes: int = 10


class ScheduleRecommendationResponse(BaseModel):
    station_code: int
    crowd_status: str
    recommended_headway_minutes: int
    dispatch_action: str
    extra_trains_needed: int
    rationale: str


class LoginRequest(BaseModel):
    email: str
    password: str
    role: str


class TrainTelemetry(BaseModel):
    service: str
    line: str
    current_station: str
    status: str
    next_arrival: str


class AlertTelemetry(BaseModel):
    type: str
    title: str
    detail: str
    time: str
    action: str


class ScheduleTelemetry(BaseModel):
    line: str
    station: str
    recommended_headway_minutes: int
    confidence: int


class OperationsTelemetryRequest(BaseModel):
    active_services: int
    trains: List[TrainTelemetry]
    alerts: List[AlertTelemetry]
    schedule: ScheduleTelemetry


class RegisterRequest(BaseModel):
    email: str
    password: str = Field(min_length=8)


def create_access_token(email: str, role: str) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRY_HOURS)
    payload = {"sub": email, "role": role, "exp": expires_at}
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def require_auth(
    credentials: HTTPAuthorizationCredentials | None = Depends(auth_scheme),
) -> dict:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        return jwt.decode(credentials.credentials, JWT_SECRET, algorithms=["HS256"])
    except jwt.PyJWTError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from error


def require_admin(current_user: dict = Depends(require_auth)) -> dict:
    if current_user.get("role") != "Admin":
        raise HTTPException(status_code=403, detail="Administrator access required.")
    return current_user


def hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    password_hash = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 120_000)
    return f"{salt.hex()}:{password_hash.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    salt_hex, password_hash_hex = stored_hash.split(":", maxsplit=1)
    calculated_hash = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), bytes.fromhex(salt_hex), 120_000
    )
    return hmac.compare_digest(calculated_hash.hex(), password_hash_hex)


def initialize_auth_db() -> None:
    global mongo_client, auth_users_collection, operations_collection

    mongo_client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
    database = mongo_client[MONGODB_DATABASE]
    auth_users_collection = database["users"]
    operations_collection = database["operations_snapshots"]
    auth_users_collection.create_index([("email", ASCENDING)], unique=True)
    operations_collection.create_index([("received_at", -1)])

    default_users = [
        (
            "admin@metroflow.com",
            os.getenv("METROFLOW_ADMIN_PASSWORD", "admin123"),
            "Admin",
        ),
        (
            "operator@metroflow.com",
            os.getenv("METROFLOW_OPERATOR_PASSWORD", "operator123"),
            "Operator",
        ),
    ]
    for email, password, role in default_users:
        auth_users_collection.update_one(
            {"email": email},
            {
                "$setOnInsert": {
                    "email": email,
                    "password_hash": hash_password(password),
                    "role": role,
                }
            },
            upsert=True,
        )


# Endpoints
@app.post("/login")
def login(data: LoginRequest):
    if auth_users_collection is None:
        raise HTTPException(status_code=503, detail="Authentication database is unavailable.")

    user = auth_users_collection.find_one({"email": data.email.lower().strip()})

    if user is None or not verify_password(data.password, user["password_hash"]):
        return {"success": False, "message": "Invalid email or password"}
    if user["role"] != data.role:
        return {"success": False, "message": "Incorrect role selected"}

    return {
        "success": True,
        "email": user["email"],
        "role": user["role"],
        "access_token": create_access_token(user["email"], user["role"]),
        "token_type": "bearer",
    }


@app.post("/register")
def register(data: RegisterRequest):
    if auth_users_collection is None:
        raise HTTPException(status_code=503, detail="Authentication database is unavailable.")

    email = data.email.lower().strip()
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        return {"success": False, "message": "Enter a valid email address."}

    try:
        auth_users_collection.insert_one(
            {
                "email": email,
                "password_hash": hash_password(data.password),
                "role": "Operator",
            }
        )
    except DuplicateKeyError:
        return {"success": False, "message": "An account with this email already exists."}

    return {"success": True, "message": "Account created. You can now sign in."}


@app.get("/api/v1/health")
def health_check(current_user: dict = Depends(require_auth)):
    return {
        "status": "healthy",
        "model_loaded": ai_model_store["weights"] is not None,
        "historical_records": len(ai_model_store["network_df"]) if ai_model_store["network_df"] is not None else 0,
        "metrics": ai_model_store["metrics"],
    }


@app.get("/api/v1/stations")
def get_station_network(current_user: dict = Depends(require_auth)):
    if ai_model_store["network_df"] is None:
        raise HTTPException(status_code=500, detail="Transit network data unavailable.")

    df = ai_model_store["network_df"]
    stations = (
        df.groupby(["station_code", "station_name", "line_name", "latitude", "longitude", "capacity"])
        .agg({"passenger_count": "mean", "entries": "mean", "exits": "mean"})
        .reset_index()
    )
    stations["avg_hourly_ridership"] = stations["passenger_count"].round().astype(int)
    return stations.to_dict(orient="records")


@app.post("/api/v1/predict/demand", response_model=PredictionResponse)
def predict_station_demand(req: PredictionRequest, current_user: dict = Depends(require_auth)):
    if ai_model_store["weights"] is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Forecasting model is not loaded.",
        )

    # Feature vector matching training order: [hour, day_of_week, is_weekend, is_peak_hour, lag_1h, lag_2h, rolling_3h]
    features = np.array([
        req.hour,
        req.day_of_week,
        req.is_weekend,
        req.is_peak_hour,
        req.lag_1h,
        req.lag_2h,
        req.rolling_3h,
    ], dtype=np.float64)

    # Bias term + dot product with regularized weights
    x_bias = np.insert(features, 0, 1.0)
    pred_val = float(np.dot(x_bias, ai_model_store["weights"]))
    pred_val = max(0, int(round(pred_val)))

    occupancy = round(min(1.0, pred_val / max(req.station_capacity, 1)), 3)
    if occupancy >= 0.8:
        crowd_lvl = "High"
    elif occupancy >= 0.5:
        crowd_lvl = "Medium"
    else:
        crowd_lvl = "Low"

    return PredictionResponse(
        station_code=req.station_code,
        predicted_passenger_demand=pred_val,
        occupancy_rate=occupancy,
        crowd_level=crowd_lvl,
        metrics=ai_model_store["metrics"],
    )


@app.get("/api/v1/operations/summary")
def get_operations_summary(current_user: dict = Depends(require_auth)):
    if operations_collection is not None:
        latest_snapshot = operations_collection.find_one(sort=[("received_at", -1)])
        if latest_snapshot is not None:
            latest_snapshot.pop("_id", None)
            return latest_snapshot

    if ai_model_store["network_df"] is None:
        raise HTTPException(status_code=500, detail="Transit network data unavailable.")

    df = ai_model_store["network_df"]
    stations = (
        df.groupby(["station_code", "station_name", "line_name", "capacity"])
        .agg({"passenger_count": "mean"})
        .reset_index()
    )
    stations["occupancy"] = stations["passenger_count"] / stations["capacity"].clip(lower=1)
    stations.sort_values("occupancy", ascending=False, inplace=True)

    trains = []
    for index, station in enumerate(stations.head(6).to_dict(orient="records")):
        load = float(station["occupancy"])
        trains.append(
            {
                "service": f"MF-{204 + index * 37}",
                "line": station["line_name"],
                "current_station": station["station_name"],
                "status": "Delayed" if load >= 0.8 else "On time",
                "next_arrival": f"{max(2, round(9 - load * 5))} min",
            }
        )

    alerts = []
    for station in stations.head(3).to_dict(orient="records"):
        load_percent = round(float(station["occupancy"]) * 100)
        if load_percent >= 80:
            alerts.append(
                {
                    "type": "critical",
                    "title": "Platform load above safe threshold",
                    "detail": f"{station['station_name']} · {station['line_name']} · Occupancy reached {load_percent}%",
                    "time": "Live",
                    "action": "Dispatch reserve",
                }
            )
        elif load_percent >= 60:
            alerts.append(
                {
                    "type": "warning",
                    "title": "Station demand requires monitoring",
                    "detail": f"{station['station_name']} · {station['line_name']} · Occupancy at {load_percent}%",
                    "time": "Live",
                    "action": "Review forecast",
                }
            )

    highest_station = stations.iloc[0].to_dict()
    highest_load = float(highest_station["occupancy"])
    recommended_headway = 3 if highest_load >= 0.85 else 5 if highest_load >= 0.65 else 8
    alerts.append(
        {
            "type": "info",
            "title": "Schedule recommendation ready",
            "detail": f"{highest_station['line_name']} · {highest_station['station_name']} · Peak window guidance",
            "time": "Live",
            "action": "Open schedule",
        }
    )

    return {
        "active_services": len(trains) * 10,
        "trains": trains,
        "alerts": alerts,
        "schedule": {
            "line": highest_station["line_name"],
            "station": highest_station["station_name"],
            "recommended_headway_minutes": recommended_headway,
            "confidence": 91,
        },
    }


@app.post("/api/v1/schedules/recommend", response_model=ScheduleRecommendationResponse)
def recommend_schedule(req: ScheduleRecommendationRequest, current_user: dict = Depends(require_auth)):
    occupancy = req.predicted_demand / max(req.station_capacity, 1)

    if occupancy >= 0.85:
        headway = 3
        action = "CRITICAL_DISPATCH"
        extra = 4
        rationale = "Severe platform congestion anticipated. Reduce headway to 3 minutes and inject 4 reserve trainsets."
        status_label = "Severe Overcrowding"
    elif occupancy >= 0.65:
        headway = 5
        action = "INCREASE_FREQUENCY"
        extra = 2
        rationale = "Elevated passenger demand detected. Shorten dispatch headway to 5 minutes to prevent platform spillover."
        status_label = "Elevated Traffic"
    elif occupancy >= 0.35:
        headway = 8
        action = "STANDARD_OPERATION"
        extra = 0
        rationale = "Passenger flow is within standard operating parameters. Maintain normal 8-minute headway."
        status_label = "Normal Flow"
    else:
        headway = 12
        action = "OPTIMIZE_EFFICIENCY"
        extra = 0
        rationale = "Low passenger footfall detected. Expand headway to 12 minutes to conserve traction energy and reduce rolling stock wear."
        status_label = "Low Footfall"

    return ScheduleRecommendationResponse(
        station_code=req.station_code,
        crowd_status=status_label,
        recommended_headway_minutes=headway,
        dispatch_action=action,
        extra_trains_needed=extra,
        rationale=rationale,
    )


@app.get("/api/v1/analytics/peak-hours")
def get_peak_hour_insights(current_user: dict = Depends(require_auth)):
    if ai_model_store["network_df"] is None:
        raise HTTPException(status_code=500, detail="Data unavailable.")

    df = ai_model_store["network_df"]
    hourly_agg = df.groupby("hour")["passenger_count"].mean().reset_index()
    hourly_agg["avg_passengers"] = hourly_agg["passenger_count"].round().astype(int)

    morning_peak = hourly_agg[(hourly_agg["hour"] >= 7) & (hourly_agg["hour"] <= 9)].sort_values(
        by="avg_passengers", ascending=False
    ).iloc[0].to_dict()

    evening_peak = hourly_agg[(hourly_agg["hour"] >= 17) & (hourly_agg["hour"] <= 20)].sort_values(
        by="avg_passengers", ascending=False
    ).iloc[0].to_dict()

    return {
        "morning_peak": {
            "hour": int(morning_peak["hour"]),
            "average_ridership": int(morning_peak["avg_passengers"]),
        },
        "evening_peak": {
            "hour": int(evening_peak["hour"]),
            "average_ridership": int(evening_peak["avg_passengers"]),
        },
        "hourly_distribution": hourly_agg[["hour", "avg_passengers"]].to_dict(orient="records"),
    }


@app.post("/api/v1/operations/telemetry")
def ingest_operations_telemetry(
    data: OperationsTelemetryRequest,
    current_user: dict = Depends(require_auth),
):
    if operations_collection is None:
        raise HTTPException(status_code=503, detail="Operations database is unavailable.")

    snapshot = data.model_dump()
    snapshot["source"] = "telemetry"
    snapshot["received_at"] = datetime.now(timezone.utc)
    operations_collection.insert_one(snapshot)
    return {
        "success": True,
        "message": "Operations telemetry stored.",
        "received_at": snapshot["received_at"],
    }


@app.get("/api/v1/admin/users")
def get_admin_users(current_user: dict = Depends(require_admin)):
    if auth_users_collection is None:
        raise HTTPException(status_code=503, detail="Authentication database is unavailable.")
    return [
        {"email": user["email"], "role": user["role"]}
        for user in auth_users_collection.find({}, {"_id": 0, "email": 1, "role": 1}).sort("email", ASCENDING)
    ]