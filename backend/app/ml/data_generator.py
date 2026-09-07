import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta, timezone

# 16 Stations across Red Line and Blue Line
STATION_METADATA = [
    # Red Line
    {"id": 1, "code": "RED-01", "name": "Central Terminal", "line": "Red Line", "capacity": 3000, "lat": 40.7128, "lng": -74.0060, "seq": 1, "interchange": True},
    {"id": 2, "code": "RED-02", "name": "Financial Plaza", "line": "Red Line", "capacity": 2500, "lat": 40.7180, "lng": -74.0010, "seq": 2, "interchange": False},
    {"id": 3, "code": "RED-03", "name": "Tech Hub North", "line": "Red Line", "capacity": 2200, "lat": 40.7250, "lng": -73.9950, "seq": 3, "interchange": False},
    {"id": 4, "code": "RED-04", "name": "University Square", "line": "Red Line", "capacity": 2000, "lat": 40.7320, "lng": -73.9900, "seq": 4, "interchange": True},
    {"id": 5, "code": "RED-05", "name": "Arts District", "line": "Red Line", "capacity": 1800, "lat": 40.7400, "lng": -73.9850, "seq": 5, "interchange": False},
    {"id": 6, "code": "RED-06", "name": "Medical Center", "line": "Red Line", "capacity": 2000, "lat": 40.7480, "lng": -73.9800, "seq": 6, "interchange": False},
    {"id": 7, "code": "RED-07", "name": "North Gate", "line": "Red Line", "capacity": 1600, "lat": 40.7560, "lng": -73.9750, "seq": 7, "interchange": False},
    {"id": 8, "code": "RED-08", "name": "Suburban North", "line": "Red Line", "capacity": 1500, "lat": 40.7640, "lng": -73.9700, "seq": 8, "interchange": False},

    # Blue Line
    {"id": 9, "code": "BLU-01", "name": "West Port", "line": "Blue Line", "capacity": 2000, "lat": 40.7100, "lng": -74.0200, "seq": 1, "interchange": False},
    {"id": 10, "code": "BLU-02", "name": "Maritime Dock", "line": "Blue Line", "capacity": 1800, "lat": 40.7115, "lng": -74.0120, "seq": 2, "interchange": False},
    {"id": 11, "code": "BLU-03", "name": "Central Terminal", "line": "Blue Line", "capacity": 3000, "lat": 40.7128, "lng": -74.0060, "seq": 3, "interchange": True},
    {"id": 12, "code": "BLU-04", "name": "Civic Center", "line": "Blue Line", "capacity": 2100, "lat": 40.7200, "lng": -73.9880, "seq": 4, "interchange": False},
    {"id": 13, "code": "BLU-05", "name": "University Square", "line": "Blue Line", "capacity": 2000, "lat": 40.7320, "lng": -73.9900, "seq": 5, "interchange": True},
    {"id": 14, "code": "BLU-06", "name": "Innovation Park", "line": "Blue Line", "capacity": 2400, "lat": 40.7380, "lng": -73.9720, "seq": 6, "interchange": False},
    {"id": 15, "code": "BLU-07", "name": "Stadium Arena", "line": "Blue Line", "capacity": 3500, "lat": 40.7450, "lng": -73.9600, "seq": 7, "interchange": False},
    {"id": 16, "code": "BLU-08", "name": "East terminus", "line": "Blue Line", "capacity": 1500, "lat": 40.7500, "lng": -73.9500, "seq": 8, "interchange": False},
]


def get_rush_hour_multiplier(hour: int, minute: int, is_weekend: bool) -> float:
    time_float = hour + minute / 60.0
    if is_weekend:
        # Weekend curve: gradual peak around 13:00 - 16:00
        return 0.4 + 0.4 * np.exp(-((time_float - 14.5) ** 2) / 8.0)
    
    # Morning peak (07:30 - 09:30)
    morning_peak = 2.5 * np.exp(-((time_float - 8.5) ** 2) / 0.8)
    # Evening peak (17:00 - 19:30)
    evening_peak = 2.8 * np.exp(-((time_float - 18.25) ** 2) / 1.0)
    # Base midday traffic
    midday = 0.8 * np.exp(-((time_float - 13.0) ** 2) / 6.0)
    # Off-peak base
    base = 0.2

    return float(np.clip(base + morning_peak + evening_peak + midday, 0.1, 3.5))


def generate_synthetic_transit_dataset(days: int = 14) -> pd.DataFrame:
    """
    Generates tabular transit dataset for ML training (15-minute aggregation intervals).
    """
    records = []
    end_time = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    start_time = end_time - timedelta(days=days)

    current = start_time
    while current <= end_time:
        hour = current.hour
        minute = current.minute
        day_of_week = current.weekday()
        is_weekend = day_of_week >= 5
        multiplier = get_rush_hour_multiplier(hour, minute, is_weekend)

        for st in STATION_METADATA:
            base_inflow = random.randint(30, 80) if not st["interchange"] else random.randint(80, 160)
            base_outflow = random.randint(25, 75) if not st["interchange"] else random.randint(70, 150)

            # Random noise & anomaly spikes (e.g. event at Stadium Arena or signal delay)
            anomaly_noise = 1.0
            if st["code"] == "BLU-07" and hour in (18, 19, 20):  # Stadium arena event
                anomaly_noise = 1.8
            elif random.random() < 0.02:  # Random sudden surge anomaly
                anomaly_noise = 2.2

            inflow = int(base_inflow * multiplier * anomaly_noise + random.randint(-5, 10))
            outflow = int(base_outflow * multiplier * (1 / anomaly_noise if anomaly_noise > 1.5 else 1.0) + random.randint(-5, 10))

            inflow = max(5, inflow)
            outflow = max(5, outflow)

            net_footfall = max(10, inflow - outflow)
            capacity = st["capacity"]
            density_pct = min(100.0, max(2.0, (net_footfall / capacity) * 100.0 * random.uniform(8.0, 12.0)))

            line_delay = 0
            if random.random() < 0.05:
                line_delay = random.choice([3, 5, 8, 12, 15])

            records.append({
                "timestamp": current.strftime("%Y-%m-%d %H:%M:%S"),
                "station_id": st["id"],
                "station_code": st["code"],
                "station_name": st["name"],
                "line_name": st["line"],
                "hour": hour,
                "minute": minute,
                "day_of_week": day_of_week,
                "is_weekend": int(is_weekend),
                "capacity": capacity,
                "inflow_ppm": inflow,
                "outflow_ppm": outflow,
                "line_delay_min": line_delay,
                "density_pct": round(density_pct, 2),
                # Targets for future horizons
                "target_inflow_15m": int(inflow * random.uniform(0.9, 1.1)),
                "target_inflow_30m": int(inflow * random.uniform(0.85, 1.15)),
                "target_inflow_60m": int(inflow * random.uniform(0.8, 1.2)),
                "target_congestion_level": "CRITICAL" if density_pct > 80 else ("MODERATE" if density_pct > 60 else "NORMAL")
            })

        current += timedelta(minutes=15)

    df = pd.DataFrame(records)
    return df


if __name__ == "__main__":
    df = generate_synthetic_transit_dataset(7)
    print(f"Generated {len(df)} synthetic transit records.")
    print(df.head())
