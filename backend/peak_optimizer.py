import pandas as pd
import numpy as np
import os

CROWD_FILE = os.path.join("data", "crowd_data.csv")
OUTPUT_FILE = os.path.join("data", "peak_hour_policy.csv")

def generate_peak_policies():
    if not os.path.exists(CROWD_FILE):
        print(f"Error: {CROWD_FILE} not found.")
        return

    df = pd.read_csv(CROWD_FILE, nrows=25000)

    # Detect timestamp column
    time_col = [c for c in df.columns if any(k in c.lower() for k in ['time', 'date'])][0]
    entry_col = [c for c in df.columns if any(k in c.lower() for k in ['entry', 'entries', 'inflow', 'board'])][0]

    df['timestamp'] = pd.to_datetime(df[time_col], errors='coerce')
    df = df.dropna(subset=['timestamp'])
    df['hour'] = df['timestamp'].dt.hour
    df['inflow'] = pd.to_numeric(df[entry_col], errors='coerce').abs().fillna(150)

    # Group by operational hour of the day
    hourly = df.groupby('hour')['inflow'].mean().round().astype(int).reset_index()

    def build_policy(row):
        hour = int(row['hour'])
        inflow = int(row['inflow'])

        # Classify transit operating periods
        if 7 <= hour <= 9:
            window = "MORNING_PEAK"
            multiplier = 1.45
            strategy = "Deploy reserve trains + short headway (3 min)"
            status = "SURGE DEMAND"
        elif 17 <= hour <= 20:
            window = "EVENING_PEAK"
            multiplier = 1.50
            strategy = "Full fleet deployment + platform metering (3 min)"
            status = "CRITICAL SURGE"
        elif 11 <= hour <= 16:
            window = "MIDDAY_OFF_PEAK"
            multiplier = 1.0
            strategy = "Standard headway (6 min) + routine maintenance"
            status = "NORMAL"
        else:
            window = "NIGHT_OFF_PEAK"
            multiplier = 0.6
            strategy = "Wide headway (10-12 min) + depot servicing"
            status = "LOW DEMAND"

        required_capacity = int(inflow * multiplier)
        return pd.Series([window, required_capacity, strategy, status])

    cols = ["time_window", "target_passenger_capacity", "fleet_strategy", "congestion_risk"]
    hourly[cols] = hourly.apply(build_policy, axis=1)

    hourly.to_csv(OUTPUT_FILE, index=False)
    print(f"Step 8 Complete: Peak-hour policies written to {OUTPUT_FILE}")

if __name__ == "__main__":
    generate_peak_policies()