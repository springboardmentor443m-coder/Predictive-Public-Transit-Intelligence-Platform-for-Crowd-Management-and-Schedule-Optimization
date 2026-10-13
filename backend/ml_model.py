import os
import random
import joblib
import numpy as np
from sklearn.ensemble import RandomForestRegressor

MODEL_FILE = "gline_demand_model.pkl"

# Complete 21 Stations for NYC Subway G-Line (Brooklyn–Queens Crosstown)
G_LINE_STATIONS = [
    "Court Sq", "21 St", "Greenpoint Av", "Nassau Av", "Metropolitan Av",
    "Broadway", "Flushing Av", "Myrtle–Willoughby Avs", "Bedford–Nostrand Avs",
    "Classon Av", "Clinton–Washington Avs", "Fulton St", "Hoyt–Schermerhorn Sts",
    "Bergen St", "Carroll St", "Smith–9th Sts", "Fourth Ave / 9th St",
    "7th Ave", "15 St–Prospect Park", "Fort Hamilton Pkwy", "Church Av"
]

def train_synthetic_model():
    """Trains a demand model for G-Line passenger load predictions."""
    np.random.seed(42)
    hours = np.random.randint(0, 24, 1200)
    days = np.random.randint(0, 7, 1200)
    is_weekend = (days >= 5).astype(int)

    occupancy = []
    for h, w in zip(hours, is_weekend):
        if (7 <= h < 10 or 16 <= h < 19) and w == 0:
            occ = random.uniform(78.0, 96.0)  # Rush hour
        elif (10 <= h < 16) and w == 0:
            occ = random.uniform(50.0, 72.0)  # Midday
        elif (19 <= h < 23 or 5 <= h < 7) and w == 0:
            occ = random.uniform(32.0, 52.0)  # Evening / Early morning
        else:
            occ = random.uniform(15.0, 32.0)  # Overnight
        occupancy.append(occ)

    X = np.column_stack((hours, days, is_weekend))
    y = np.array(occupancy)

    model = RandomForestRegressor(n_estimators=30, random_state=42)
    model.fit(X, y)

    joblib.dump(model, MODEL_FILE)
    print("✅ In-Memory G-Line AI Model trained successfully!")
    return model


def get_schedule_period_data(hour: int, day_of_week: int = 1) -> dict:
    """Returns frequency, active fleet count, and status based on time of day."""
    if os.path.exists(MODEL_FILE):
        model = joblib.load(MODEL_FILE)
    else:
        model = train_synthetic_model()

    is_weekend = 1 if day_of_week >= 5 else 0
    pred_occ = float(model.predict([[hour, day_of_week, is_weekend]])[0])
    pred_occ = round(min(max(pred_occ, 15.0), 98.0), 1)

    if 7 <= hour < 10:
        period = "Morning Rush Hour (7:00 AM – 9:30 AM)"
        headway = 5
        active_trains = 47  # 42 standard + 5 peak extras
        status = "RED"
        action = "PEAK SERVICE: +5 Peak Trains deployed. 5-min headway active."
    elif 16 <= hour < 19:
        period = "Evening Rush Hour (4:00 PM – 7:00 PM)"
        headway = 5
        active_trains = 47  # 42 standard + 5 peak extras
        status = "RED"
        action = "PEAK SERVICE: +5 Peak Trains deployed. 5-min headway active."
    elif 10 <= hour < 16:
        period = "Midday Off-Peak (9:30 AM – 4:00 PM)"
        headway = 8
        active_trains = 42
        status = "YELLOW"
        action = "MIDDAY SERVICE: Standard 42 trains operating at 8-min headway."
    elif 19 <= hour < 23 or 5 <= hour < 7:
        period = "Late Evening / Early Morning"
        headway = 10
        active_trains = 36
        status = "YELLOW"
        action = "MODERATE SERVICE: 36 trains operating at 10-min headway."
    else:
        period = "Overnight / Late Night (11:00 PM – 5:00 AM)"
        headway = 20
        active_trains = 20
        status = "GREEN"
        action = "OVERNIGHT SERVICE: Reduced night fleet at 20-min headway."

    return {
        "hour": hour,
        "period_name": period,
        "predicted_occupancy_pct": pred_occ,
        "recommended_headway_min": headway,
        "active_train_count": active_trains,
        "status": status,
        "action": action
    }

if __name__ == "__main__":
    train_synthetic_model()