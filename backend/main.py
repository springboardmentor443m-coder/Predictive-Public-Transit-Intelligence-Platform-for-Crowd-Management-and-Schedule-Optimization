import os
import csv
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

try:
    from pymongo import MongoClient
except ModuleNotFoundError:
    MongoClient = None


# --------------------------------------------------
# APP CONFIGURATION
# --------------------------------------------------

app = FastAPI(
    title="MetroFlow API",
    description="AI Predictive Public Transit Intelligence Platform",
    version="1.0.0"
)




app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# LOGIN REQUEST MODEL
# --------------------------------------------------

class LoginRequest(BaseModel):
    email: str
    password: str
    role: str


class PassengerRecord(BaseModel):
    station_id: str
    station_name: str
    timestamp: datetime
    entries: int = Field(ge=0)
    exits: int = Field(ge=0)
    passenger_count: int | None = Field(default=None, ge=0)


class Station(BaseModel):
    station_id: str
    name: str
    capacity: int = Field(gt=0)
    latitude: float | None = None
    longitude: float | None = None


MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://127.0.0.1:27017")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "metroflow")
mongo_client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=3000) if MongoClient else None
database = mongo_client[MONGODB_DATABASE] if mongo_client else None
stations_collection = database["stations"] if database is not None else None
passenger_records_collection = database["passenger_records"] if database is not None else None

LOCAL_STATIONS: list[dict[str, Any]] = []
LOCAL_PASSENGER_RECORDS: list[dict[str, Any]] = []

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CSV_SOURCE_PATH = Path(
    os.getenv(
        "METROFLOW_CSV_PATH",
        PROJECT_ROOT / "data" / "nyc_subway_ridership_sample.csv",
    )
)

DEFAULT_STATIONS = [
    {"station_id": "ST001", "name": "Central Station", "capacity": 1000, "latitude": 40.7527, "longitude": -73.9772},
    {"station_id": "ST002", "name": "City Square", "capacity": 900, "latitude": 40.7420, "longitude": -73.9896},
    {"station_id": "ST003", "name": "North Station", "capacity": 700, "latitude": 40.7648, "longitude": -73.9808},
    {"station_id": "ST004", "name": "Airport Station", "capacity": 1200, "latitude": 40.6413, "longitude": -73.7781},
]

DEFAULT_PASSENGER_RECORDS = [
    {"station_id": "ST001", "station_name": "Central Station", "entries": 500, "exits": 350, "passenger_count": 850},
    {"station_id": "ST002", "station_name": "City Square", "entries": 230, "exits": 190, "passenger_count": 420},
    {"station_id": "ST003", "station_name": "North Station", "entries": 80, "exits": 70, "passenger_count": 150},
    {"station_id": "ST004", "station_name": "Airport Station", "entries": 390, "exits": 290, "passenger_count": 680},
]


def initialize_database():
    if mongo_client is None:
        load_local_data()
        return

    try:
        mongo_client.admin.command("ping")
        station_schema_is_valid = stations_collection.count_documents(
            {"station_id": {"$exists": True}, "capacity": {"$exists": True}}
        ) == stations_collection.count_documents({})
        if not station_schema_is_valid:
            load_local_data()
            return
        if stations_collection.count_documents({}) == 0:
            stations_collection.insert_many(DEFAULT_STATIONS)
        if passenger_records_collection.count_documents({}) == 0:
            passenger_records_collection.insert_many(
                {**record, "timestamp": datetime.now().isoformat()}
                for record in DEFAULT_PASSENGER_RECORDS
            )
    except Exception:
        load_local_data()


def load_local_data():
    if LOCAL_STATIONS:
        return

    if CSV_SOURCE_PATH.exists():
        stations, records = load_turnstile_csv(CSV_SOURCE_PATH)
        if stations:
            LOCAL_STATIONS.extend(stations)
            LOCAL_PASSENGER_RECORDS.extend(records)
            return

    LOCAL_STATIONS.extend(DEFAULT_STATIONS)
    LOCAL_PASSENGER_RECORDS.extend(
        {**record, "timestamp": datetime.now().isoformat()}
        for record in DEFAULT_PASSENGER_RECORDS
    )


def load_turnstile_csv(path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Load cumulative MTA turnstile readings as hourly flow records."""
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))

    required_columns = {"unit", "scp", "station", "date", "time", "entries", "exits"}
    if not rows or not required_columns.issubset(rows[0]):
        return [], []

    rows.sort(key=lambda row: (row["unit"], row["scp"], row["date"], row["time"]))
    previous: dict[tuple[str, str], tuple[int, int]] = {}
    station_totals: dict[str, dict[str, Any]] = {}
    records: list[dict[str, Any]] = []

    for row in rows:
        key = (row["unit"], row["scp"])
        current_entries = int(float(row["entries"]))
        current_exits = int(float(row["exits"]))
        old_entries, old_exits = previous.get(key, (current_entries, current_exits))
        entries = max(current_entries - old_entries, 0)
        exits = max(current_exits - old_exits, 0)
        previous[key] = (current_entries, current_exits)

        station_name = row["station"].strip()
        station_id = f"MTA-{station_name.upper().replace(' ', '-')}"
        station_totals.setdefault(
            station_id,
            {"station_id": station_id, "name": station_name, "capacity": 1000},
        )
        records.append(
            {
                "station_id": station_id,
                "station_name": station_name,
                "timestamp": f"{row['date'][:10]}T{row['time']}",
                "entries": entries,
                "exits": exits,
                "passenger_count": entries,
            }
        )

    return list(station_totals.values()), records


def get_stations_collection():
    return stations_collection if not LOCAL_STATIONS else LOCAL_STATIONS


def get_passenger_records_collection():
    return passenger_records_collection if not LOCAL_STATIONS else LOCAL_PASSENGER_RECORDS


def crowd_level(occupancy_rate: float) -> str:
    if occupancy_rate > 0.8:
        return "High"
    if occupancy_rate >= 0.5:
        return "Medium"
    return "Low"


def station_snapshot(station: dict[str, Any], record: dict[str, Any] | None) -> dict[str, Any]:
    entries = int(record.get("entries", 0)) if record else 0
    exits = int(record.get("exits", 0)) if record else 0
    passengers = int(record.get("passenger_count", entries)) if record else 0
    occupancy_rate = passengers / station["capacity"]
    level = crowd_level(occupancy_rate)
    return {
        "station_id": station["station_id"],
        "name": station["name"],
        "passengers": passengers,
        "inflow": entries,
        "outflow": exits,
        "capacity": station["capacity"],
        "occupancy_rate": round(occupancy_rate, 3),
        "crowd": level,
        "status": "Congested" if level == "High" else "Normal",
    }


initialize_database()


# --------------------------------------------------
# HOME / HEALTH CHECK
# --------------------------------------------------

@app.get("/")
def home():
    return {
        "message": "MetroFlow API is running",
        "status": "success"
    }


@app.get("/health")
def health():
    return {"status": "healthy", "database": "local" if LOCAL_STATIONS else "mongodb"}


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return Response(status_code=204)


# --------------------------------------------------
# AUTHENTICATION
# --------------------------------------------------

@app.post("/login")
def login(data: LoginRequest):

    users = {
        "admin@metroflow.com": {
            "password": "admin123",
            "role": "Admin"
        },
        "operator@metroflow.com": {
            "password": "operator123",
            "role": "Operator"
        }
    }

    # Check email
    user = users.get(data.email)

    if user is None:
        return {
            "success": False,
            "message": "User not found"
        }

    # Check password
    if user["password"] != data.password:
        return {
            "success": False,
            "message": "Incorrect password"
        }

    # Check selected role
    if user["role"] != data.role:
        return {
            "success": False,
            "message": "Incorrect role selected"
        }

    # Successful login
    return {
        "success": True,
        "message": "Login successful",
        "role": user["role"],
        "email": data.email
    }


@app.post("/stations", status_code=201)
def create_station(station: Station):
    station_data = station.model_dump()
    response_data = station_data.copy()
    collection = get_stations_collection()
    if isinstance(collection, list):
        if any(item["station_id"] == station.station_id for item in collection):
            raise HTTPException(status_code=409, detail="Station already exists")
        collection.append(station_data)
    else:
        if collection.find_one({"station_id": station.station_id}):
            raise HTTPException(status_code=409, detail="Station already exists")
        collection.insert_one(station_data)
    return {"success": True, "station": response_data}


@app.get("/stations")
def get_stations():
    if LOCAL_STATIONS:
        stations = LOCAL_STATIONS
        records = LOCAL_PASSENGER_RECORDS
    else:
        stations = list(stations_collection.find({}, {"_id": 0}))
        records = list(passenger_records_collection.find({}, {"_id": 0}))

    return [
        station_snapshot(
            station,
            next((record for record in reversed(records) if record["station_id"] == station["station_id"]), None),
        )
        for station in stations
    ]


@app.post("/passenger-records", status_code=201)
def create_passenger_record(record: PassengerRecord):
    record_data = record.model_dump()
    record_data["timestamp"] = record.timestamp.isoformat()
    response_data = record_data.copy()
    collection = get_passenger_records_collection()
    if isinstance(collection, list):
        collection.append(record_data)
    else:
        collection.insert_one(record_data)
    return {"success": True, "record": response_data}


@app.get("/analytics/summary")
def analytics_summary():
    snapshots = get_stations()
    return {
        "station_count": len(snapshots),
        "total_passengers": sum(station["passengers"] for station in snapshots),
        "high_crowd_stations": sum(station["crowd"] == "High" for station in snapshots),
        "congested_stations": sum(station["status"] == "Congested" for station in snapshots),
    }