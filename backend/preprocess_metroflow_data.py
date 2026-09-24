from pathlib import Path
import pandas as pd
import numpy as np

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
OUTPUT_FILE = DATA_DIR / "metroflow_processed_network.csv"

print("Step 1: Reading station metadata...")
station_info = pd.read_csv(
    DATA_DIR / "seoul-metro-station-info.csv",
    usecols=[
        "station.code",
        "station.name_en",
        "line.name",
        "geo.latitude",
        "geo.longitude",
    ],
)
station_info.rename(
    columns={
        "station.code": "station_code",
        "station.name_en": "station_name",
        "line.name": "line_name",
        "geo.latitude": "latitude",
        "geo.longitude": "longitude",
    },
    inplace=True,
)
station_info.drop_duplicates(subset=["station_code"], inplace=True)

# Select the top 12 representative major transit stations for clean operational intelligence
top_stations = station_info.head(12)
top_station_codes = set(top_stations["station_code"].tolist())

print(f"Tracking {len(top_stations)} major metro stations across lines.")

print("Step 2: Processing ridership logs for 2021...")
# Read logs for the selected top stations across 60 representative days
logs_chunk_list = []
chunk_size = 100_000

for chunk in pd.read_csv(DATA_DIR / "seoul-metro-2021.logs.csv", chunksize=chunk_size):
    filtered = chunk[chunk["station_code"].isin(top_station_codes)].copy()
    if not filtered.empty:
        logs_chunk_list.append(filtered)
    # Stop once we have sufficient historical records for explainable ML training
    if sum(len(c) for c in logs_chunk_list) >= 25_000:
        break

df_logs = pd.concat(logs_chunk_list, ignore_index=True)
print(f"Loaded {len(df_logs)} hourly station observation records.")

print("Step 3: Merging logs with station spatial metadata...")
merged = pd.merge(df_logs, top_stations, on="station_code", how="inner")

print("Step 4: Engineering time and flow features...")
# Clean ISO timestamp
merged["timestamp"] = pd.to_datetime(merged["timestamp"])
merged["date"] = merged["timestamp"].dt.strftime("%Y-%m-%d")
merged["hour"] = merged["timestamp"].dt.hour
merged["day_of_week"] = merged["timestamp"].dt.dayofweek
merged["is_weekend"] = (merged["day_of_week"] >= 5).astype(int)

# Inflow, Outflow, Passenger Total
merged["entries"] = merged["people_in"].fillna(0).astype(int)
merged["exits"] = merged["people_out"].fillna(0).astype(int)
merged["passenger_count"] = merged["entries"] + merged["exits"]

# Capacity baseline per station (scaled from historical 95th percentile peak)
station_peak = (
    merged.groupby("station_code")["passenger_count"]
    .quantile(0.95)
    .to_dict()
)
merged["capacity"] = merged["station_code"].map(
    lambda code: int(max(station_peak.get(code, 1500) * 1.15, 800))
)

# Operational Occupancy Rate & Congestion Status
merged["occupancy_rate"] = np.round(merged["passenger_count"] / merged["capacity"], 3)
merged["occupancy_rate"] = merged["occupancy_rate"].clip(upper=1.0)

merged["crowd_level"] = "Low"
merged.loc[merged["occupancy_rate"] >= 0.5, "crowd_level"] = "Medium"
merged.loc[merged["occupancy_rate"] >= 0.8, "crowd_level"] = "High"

# Peak hour indicator (morning rush: 7-9, evening rush: 17-20 on weekdays)
merged["is_peak_hour"] = (
    (merged["is_weekend"] == 0)
    & (
        ((merged["hour"] >= 7) & (merged["hour"] <= 9))
        | ((merged["hour"] >= 17) & (merged["hour"] <= 20))
    )
).astype(int)

# Sort chronologically by station and time
merged.sort_values(by=["station_code", "timestamp"], inplace=True)
merged.reset_index(drop=True, inplace=True)

# Export clean unified dataset
merged.to_csv(OUTPUT_FILE, index=False)
print(f"\n[SUCCESS] Clean MetroFlow dataset saved to: {OUTPUT_FILE}")
print(f"Total Rows: {len(merged)} | Columns: {len(merged.columns)}")
print("Sample Columns:", merged.columns.tolist()[:8])