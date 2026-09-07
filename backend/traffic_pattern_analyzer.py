import pandas as pd
import numpy as np
import os

CROWD_FILE = os.path.join("data", "crowd_data.csv")
OUTPUT_FILE = os.path.join("data", "traffic_patterns.csv")

def analyze_traffic_patterns():
    if not os.path.exists(CROWD_FILE):
        print(f"Error: {CROWD_FILE} not found.")
        return

    df = pd.read_csv(CROWD_FILE, nrows=35000)

    # Detect station, time, and entry/exit columns
    station_col = [c for c in df.columns if any(k in c.lower() for k in ['station', 'stop', 'unit'])][0]
    time_col = [c for c in df.columns if any(k in c.lower() for k in ['time', 'date'])][0]
    entry_col = [c for c in df.columns if any(k in c.lower() for k in ['entry', 'entries', 'inflow', 'board'])][0]
    exit_col = [c for c in df.columns if any(k in c.lower() for k in ['exit', 'exits', 'outflow', 'alight'])][0]

    df['timestamp'] = pd.to_datetime(df[time_col], errors='coerce')
    df = df.dropna(subset=['timestamp'])
    df['hour'] = df['timestamp'].dt.hour
    df['inflow'] = pd.to_numeric(df[entry_col], errors='coerce').abs().fillna(100)
    df['outflow'] = pd.to_numeric(df[exit_col], errors='coerce').abs().fillna(80)

    # Categorize into time windows
    def assign_bucket(hour):
        if 6 <= hour <= 9:
            return "Morning Rush"
        elif 10 <= hour <= 15:
            return "Midday Flow"
        elif 16 <= hour <= 20:
            return "Evening Rush"
        return "Night Service"

    df['time_segment'] = df['hour'].apply(assign_bucket)

    # Group by station and operational segment
    pattern = df.groupby([station_col, 'time_segment']).agg({
        'inflow': ['mean', 'max', 'std'],
        'outflow': ['mean', 'max']
    }).reset_index()

    pattern.columns = ['station_id', 'time_segment', 'avg_inflow', 'peak_inflow', 'flow_volatility', 'avg_outflow', 'peak_outflow']

    pattern['avg_inflow'] = pattern['avg_inflow'].round().astype(int)
    pattern['peak_inflow'] = pattern['peak_inflow'].round().astype(int)
    pattern['avg_outflow'] = pattern['avg_outflow'].round().astype(int)
    pattern['peak_outflow'] = pattern['peak_outflow'].round().astype(int)
    pattern['flow_volatility'] = pattern['flow_volatility'].fillna(0.0).round(1)

    # Identify bottleneck tendencies
    def classify_bottleneck(row):
        if row['peak_inflow'] > 2200 or row['avg_inflow'] > 1400:
            return "CHRONIC BOTTLENECK"
        elif row['peak_inflow'] > 1200:
            return "SURGE PRONE"
        return "STABLE FLOW"

    pattern['bottleneck_profile'] = pattern.apply(classify_bottleneck, axis=1)

    pattern.head(20).to_csv(OUTPUT_FILE, index=False)
    print(f"Step 10 Complete: Traffic patterns generated at {OUTPUT_FILE}")

if __name__ == "__main__":
    analyze_traffic_patterns()