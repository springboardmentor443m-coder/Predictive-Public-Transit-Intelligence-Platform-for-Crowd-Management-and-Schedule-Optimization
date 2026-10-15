import os
import pickle
from datetime import datetime
from fastapi import APIRouter
from app.core.database import get_database

router = APIRouter(prefix="/api/schedule", tags=["Predictive Fleet & Headway Dispatch"])

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "..", "..", "ml", "models", "crowd_predictor.pkl")

# Load model data
forest_model = None
if os.path.exists(MODEL_PATH):
    with open(MODEL_PATH, "rb") as f:
        forest_model = pickle.load(f)
    print(f"[✓] Loaded Random Forest Model successfully from {MODEL_PATH}")

def predict_single_tree(node, row):
    if "val" in node:
        return node["val"]
    if row[node["feat"]] <= node["th"]:
        return predict_single_tree(node["left"], row)
    return predict_single_tree(node["right"], row)

def predict_crowd(features_row):
    if not forest_model or "trees" not in forest_model:
        return 500.0  # Fallback
    tree_vals = [predict_single_tree(t, features_row) for t in forest_model["trees"]]
    return sum(tree_vals) / len(tree_vals)

CORRIDORS = [
    {"corridor": "Blue Corridor", "line_name": "1호선", "default_headway": 5.0, "station_codes": [150, 151, 152, 153]},
    {"corridor": "Emerald Express", "line_name": "2호선", "default_headway": 6.5, "station_codes": [201, 202]},
    {"corridor": "Ruby Loop", "line_name": "1호선 Branch", "default_headway": 8.0, "station_codes": [154, 155, 156]}
]

@router.get("/dispatch")
async def get_predictive_dispatch():
    db = get_database()
    logs_col = db["turnstile_logs"]

    now = datetime.now()
    current_hour = now.hour
    is_weekend = 1 if now.weekday() >= 5 else 0
    is_peak = 1 if (7 <= current_hour <= 9 or 17 <= current_hour <= 20) else 0

    dispatch_cards = []

    for c in CORRIDORS:
        latest_record = await logs_col.find_one(
            {"station_code": {"$in": c["station_codes"]}},
            sort=[("_id", -1)]
        )

        exits = float(latest_record.get("exits", 250)) if latest_record else 250.0
        primary_station = c["station_codes"][0]

        # Random Forest prediction call
        features = [primary_station, current_hour, now.weekday(), is_weekend, is_peak, exits]
        predicted_inflow = predict_crowd(features)

        # Dynamic Headway logic
        if predicted_inflow > 1200 or is_peak:
            rec_headway = max(2.5, round(c["default_headway"] * 0.5, 1))
            status = "ACTION NEEDED"
        elif predicted_inflow > 600:
            rec_headway = max(3.5, round(c["default_headway"] * 0.75, 1))
            status = "ACTION NEEDED"
        else:
            rec_headway = c["default_headway"]
            status = "BALANCED"

        dispatch_cards.append({
            "corridor": c["corridor"],
            "current_headway": f"{c['default_headway']}m",
            "recommended_headway": f"{rec_headway}m",
            "status": status,
            "predicted_surge_per_min": int(predicted_inflow / 60),
            "peak_forecast_per_hr": int(predicted_inflow)
        })

    return {
        "timestamp": now.isoformat(),
        "schedules": dispatch_cards
    }