import pandas as pd
import numpy as np
import os

DATA_DIR = "data"
NYC_FILE = os.path.join(DATA_DIR, "crowd_data.csv")
MULTI_CITY_FILE = os.path.join(DATA_DIR, "schedule_data.csv")

def clean_nyc_crowd_data():
    if not os.path.exists(NYC_FILE):
        print(f"[!] Warning: {NYC_FILE} not found. Skipping NYC Subway cleaning.")
        return

    print("Cleaning NYC Subway Crowd Data...")
    df = pd.read_csv(NYC_FILE, nrows=50000)

    # 1. Standardize column names
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    # 2. Identify core columns flexibly
    stn_col = next((c for c in df.columns if any(k in c for k in ['station', 'stop', 'unit'])), 'station')
    entry_col = next((c for c in df.columns if any(k in c for k in ['entries', 'entry', 'inflow', 'board'])), 'entries')
    exit_col = next((c for c in df.columns if any(k in c for k in ['exits', 'exit', 'outflow', 'alight'])), 'exits')

    # 3. Clean string values & drop null IDs
    df[stn_col] = df[stn_col].astype(str).str.strip().str.upper()
    df = df.dropna(subset=[stn_col])

    # 4. Remove negative counts and impossible counter spikes (outliers > 15,000/hr)
    df[entry_col] = pd.to_numeric(df[entry_col], errors='coerce').fillna(0)
    df[exit_col] = pd.to_numeric(df[exit_col], errors='coerce').fillna(0)

    df = df[(df[entry_col] >= 0) & (df[entry_col] <= 15000)]
    df = df[(df[exit_col] >= 0) & (df[exit_col] <= 15000)]

    # 5. Build clean live_crowd_summary.csv
    summary = df.groupby(stn_col).agg(
        inflow=(entry_col, 'mean'),
        outflow=(exit_col, 'mean')
    ).reset_index()

    summary.rename(columns={stn_col: "station_id"}, inplace=True)
    summary["inflow"] = summary["inflow"].round().astype(int)
    summary["outflow"] = summary["outflow"].round().astype(int)
    summary["net_occupancy"] = summary["inflow"] - summary["outflow"]

    # Assign clean congestion states
    def tag_congestion(net):
        if net > 1800: return "CRITICAL"
        if net > 1000: return "HIGH"
        if net > 400:  return "MODERATE"
        return "NORMAL"

    summary["congestion_level"] = summary["net_occupancy"].apply(tag_congestion)

    output_path = os.path.join(DATA_DIR, "live_crowd_summary.csv")
    summary.head(30).to_csv(output_path, index=False)
    print(f" Cleaned live crowd data saved to {output_path}")


def clean_multicity_schedule_data():
    if not os.path.exists(MULTI_CITY_FILE):
        print(f"[!] Warning: {MULTI_CITY_FILE} not found. Skipping Multi-City cleaning.")
        return

    print("Cleaning Multi-City Schedule & Transit Data...")
    df = pd.read_csv(MULTI_CITY_FILE, nrows=50000)

    # 1. Standardize column names
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    # 2. Identify key columns
    route_col = next((c for c in df.columns if any(k in c for k in ['route', 'line', 'transit'])), 'route_id')
    delay_col = next((c for c in df.columns if 'delay' in c), 'delay_minutes')
    occ_col = next((c for c in df.columns if any(k in c for k in ['occupancy', 'capacity', 'load'])), 'occupancy')

    # 3. Clean numeric fields: clamp occupancy 0-100%, delay >= 0
    df[delay_col] = pd.to_numeric(df[delay_col], errors='coerce').fillna(0).abs()
    df[occ_col] = pd.to_numeric(df[occ_col], errors='coerce').fillna(50)
    
    # If occupancy is decimal (e.g. 0.82), convert to percentage (82)
    if df[occ_col].max() <= 1.0:
        df[occ_col] = df[occ_col] * 100
    df[occ_col] = df[occ_col].clip(0, 100)

    # 4. Aggregate clean active_schedules.csv
    clean_schedules = df.groupby(route_col).agg(
        delay_minutes=(delay_col, 'mean'),
        occupancy_pct=(occ_col, 'mean')
    ).reset_index()

    clean_schedules.rename(columns={route_col: "route_id"}, inplace=True)
    clean_schedules["delay_minutes"] = clean_schedules["delay_minutes"].round(1)
    clean_schedules["occupancy_pct"] = clean_schedules["occupancy_pct"].round(1)

    def set_status(d):
        if d >= 5.0: return "CRITICAL DELAY"
        if d >= 2.0: return "MODERATE DELAY"
        return "ON TIME"

    clean_schedules["status"] = clean_schedules["delay_minutes"].apply(set_status)

    output_path = os.path.join(DATA_DIR, "active_schedules.csv")
    clean_schedules.head(20).to_csv(output_path, index=False)
    print(f" Cleaned schedule data saved to {output_path}")

if __name__ == "__main__":
    clean_nyc_crowd_data()
    clean_multicity_schedule_data()