"""
backend/main.py (v3)
FastAPI backend for MetroFlow - capacity-based crowd logic, simulated
operational layers, two alert types, and analytics endpoints.

Run (from the backend/ folder):
  uvicorn main:app --reload --port 8000
Then visit http://localhost:8000/docs for interactive API docs.
"""

import re
import sys
import os
import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "model"))
from scheduling import (  # noqa: E402
    build_capacity_table, crowd_percent, crowd_level, recommendation,
    simulate_next_arrivals, simulate_delay_minutes, delay_alert,
)

app = FastAPI(title="MetroFlow API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "model", "metroflow_model.joblib")
DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "metroflow_final.csv")

bundle = joblib.load(MODEL_PATH)
model = bundle["model"]
station_encoder = bundle["station_encoder"]
day_encoder = bundle["day_encoder"]
bucket_encoder = bundle["bucket_encoder"]
station_lookup = bundle["station_lookup"]

STATION_NAMES = list(station_encoder.classes_)

# Real data, used to build the capacity table and traffic-pattern aggregates
raw_df = pd.read_csv(DATA_PATH)
CAPACITY_TABLE = build_capacity_table(raw_df)

# In-memory emergency broadcast (resets on server restart - fine for this scope)
_broadcast = {"message": None}


def time_bucket(hour):
    if 8 <= hour <= 10:
        return "morning_peak"
    elif 17 <= hour <= 19:
        return "evening_peak"
    elif 11 <= hour <= 16:
        return "midday"
    else:
        return "off_peak"


def day_name_from_weekend_flag(is_weekend):
    return "Saturday" if is_weekend else "Wednesday"


def predict_crowd(station: str, hour: int, is_weekend: int = 0, is_holiday: int = 0) -> int:
    if station not in STATION_NAMES:
        raise HTTPException(status_code=404, detail=f"Unknown station '{station}'")
    if not (0 <= hour <= 23):
        raise HTTPException(status_code=400, detail="hour must be between 0 and 23")

    station_encoded = station_encoder.transform([station])[0]
    bucket_encoded = bucket_encoder.transform([time_bucket(hour)])[0]
    day_encoded = day_encoder.transform([day_name_from_weekend_flag(is_weekend)])[0]

    X = pd.DataFrame(
        [[hour, is_weekend, is_holiday, station_encoded, day_encoded, bucket_encoded]],
        columns=["hour", "is_weekend", "is_holiday", "station_encoded",
                 "day_of_week_encoded", "time_bucket_encoded"],
    )
    return int(model.predict(X)[0])


def full_station_result(station: str, hour: int, is_weekend: int = 0, is_holiday: int = 0) -> dict:
    pred = predict_crowd(station, hour, is_weekend, is_holiday)
    rec = recommendation(pred, station, CAPACITY_TABLE)
    delay = simulate_delay_minutes(rec["crowd_pct"], seed=hash((station, hour)) % 10000)
    row = station_lookup[station_lookup["station"] == station].iloc[0]
    return {
        "station": station,
        "lat": row["lat"],
        "lon": row["lon"],
        "hour": hour,
        "predicted_passenger_count": pred,
        "capacity": CAPACITY_TABLE.get(station),
        **rec,
        "simulated_delay_min": delay,
        "delay_alert": delay_alert(delay),
        "next_arrivals_min": simulate_next_arrivals(hour),
    }


@app.get("/")
def root():
    return {"status": "MetroFlow API running", "stations": len(STATION_NAMES)}


@app.get("/stations")
def get_stations():
    return station_lookup.to_dict(orient="records")


@app.get("/predict")
def predict(station: str, hour: int, is_weekend: int = 0, is_holiday: int = 0):
    return full_station_result(station, hour, is_weekend, is_holiday)


@app.get("/predict_all")
def predict_all(hour: int, is_weekend: int = 0, is_holiday: int = 0):
    return [full_station_result(s, hour, is_weekend, is_holiday) for s in STATION_NAMES]


@app.get("/traffic_patterns")
def traffic_patterns():
    """Average ridership by hour and by day of week, across all stations - for the dashboard's traffic pattern charts."""
    by_hour = raw_df.groupby("hour")["passenger_count"].mean().round().to_dict()
    by_day = raw_df.groupby("day_of_week")["passenger_count"].mean().round().to_dict()
    return {"by_hour": by_hour, "by_day": by_day}


@app.get("/station_report")
def station_report():
    """Per-station summary: peak hour, average crowd %, how often it hits 'high'."""
    report = []
    for station in STATION_NAMES:
        sdf = raw_df[raw_df["station"] == station]
        capacity = CAPACITY_TABLE[station]
        crowd_pcts = 100 * sdf["passenger_count"] / capacity
        peak_row = sdf.loc[sdf["passenger_count"].idxmax()]
        report.append({
            "station": station,
            "capacity": capacity,
            "peak_hour": int(peak_row["hour"]),
            "peak_passenger_count": int(peak_row["passenger_count"]),
            "avg_crowd_pct": round(crowd_pcts.mean(), 1),
            "pct_hours_high": round(100 * (crowd_pcts >= 80).mean(), 2),
        })
    return report


@app.get("/broadcast")
def get_broadcast():
    return {"message": _broadcast["message"]}


@app.post("/broadcast")
def post_broadcast(message: str, role: str = "operator"):
    """Admin-only emergency broadcast. role must be 'admin'."""
    if role != "admin":
        raise HTTPException(status_code=403, detail="Only admin can post a broadcast.")
    _broadcast["message"] = message
    return {"status": "posted", "message": message}


@app.delete("/broadcast")
def clear_broadcast(role: str = "operator"):
    if role != "admin":
        raise HTTPException(status_code=403, detail="Only admin can clear a broadcast.")
    _broadcast["message"] = None
    return {"status": "cleared"}


@app.get("/query")
def query(text: str):
    """
    Natural-language query. Extracts a station + hour with pattern
    matching, gets a REAL prediction from the trained model, and
    phrases a plain-English answer. The model always supplies the
    number; this endpoint only phrases it.
    """
    text_lower = text.lower()

    matched_station = None
    for name in STATION_NAMES:
        if name.lower() in text_lower:
            matched_station = name
            break
    if not matched_station:
        return {"answer": f"I couldn't find a station name in your question. Try one of: {', '.join(STATION_NAMES)}."}

    hour = 18
    am_pm_match = re.search(r"(\d{1,2})\s*(am|pm)", text_lower)
    hm24_match = re.search(r"(\d{1,2}):00", text_lower)
    if am_pm_match:
        h = int(am_pm_match.group(1))
        if am_pm_match.group(2) == "pm" and h != 12:
            h += 12
        hour = h
    elif hm24_match:
        hour = int(hm24_match.group(1))

    is_weekend = 1 if "weekend" in text_lower else 0
    result = full_station_result(matched_station, hour, is_weekend)

    answer = (
        f"{matched_station} at {hour}:00 is predicted at {result['crowd_pct']}% of capacity "
        f"(~{result['predicted_passenger_count']} passengers, {result['level']} crowd level). "
        f"{result['message']} Estimated delay: {result['simulated_delay_min']} min."
    )
    return {"answer": answer, **result}
