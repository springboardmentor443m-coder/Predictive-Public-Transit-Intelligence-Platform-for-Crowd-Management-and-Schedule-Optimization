import pandas as pd

schedule_path = "data/raw/mta_schedule_2025_05_05.csv"
mapping_path = "data/processed/station_mapping.csv"
output_path = "data/processed/station_hourly_schedule_2025_05_05.csv"

schedule = pd.read_csv(schedule_path)
mapping = pd.read_csv(mapping_path)

print("Schedule rows:", len(schedule))
print("Mapping rows:", len(mapping))

# Convert data types
schedule["revenue_service"] = pd.to_numeric(
    schedule["revenue_service"],
    errors="coerce"
)

schedule["departure_time"] = pd.to_datetime(
    schedule["departure_time"],
    errors="coerce"
)

# Keep only revenue-service trains
schedule = schedule[
    schedule["revenue_service"] == 1
].copy()

schedule = schedule.dropna(
    subset=[
        "departure_time",
        "gtfs_stop_id",
        "train_id"
    ]
)

print("Rows after cleaning:", len(schedule))

# Prepare station mapping
mapping["complex_id"] = pd.to_numeric(
    mapping["complex_id"],
    errors="coerce"
)

mapping = mapping.dropna(
    subset=[
        "complex_id",
        "gtfs_stop_id"
    ]
)

mapping["complex_id"] = mapping["complex_id"].astype("int64")

stop_mapping = mapping[
    ["gtfs_stop_id", "complex_id"]
].drop_duplicates()

# Map every GTFS stop to its station complex
schedule = schedule.merge(
    stop_mapping,
    on="gtfs_stop_id",
    how="inner"
)

print("Rows after station mapping:", len(schedule))

# Convert departure time to hourly timestamp
schedule["timestamp_hour"] = (
    schedule["departure_time"].dt.floor("h")
)

# Count unique trains at each station complex per hour
hourly = (
    schedule
    .groupby(
        [
            "timestamp_hour",
            "complex_id"
        ]
    )["train_id"]
    .nunique()
    .reset_index(
        name="scheduled_trains"
    )
)

hourly = hourly.rename(
    columns={
        "timestamp_hour": "transit_timestamp",
        "complex_id": "station_complex_id"
    }
)

# Add station information
station_info = (
    mapping[
        [
            "complex_id",
            "stop_name",
            "borough"
        ]
    ]
    .drop_duplicates("complex_id")
    .rename(
        columns={
            "complex_id": "station_complex_id",
            "stop_name": "station_name"
        }
    )
)

hourly = hourly.merge(
    station_info,
    on="station_complex_id",
    how="left"
)

hourly = hourly.sort_values(
    [
        "transit_timestamp",
        "station_complex_id"
    ]
).reset_index(drop=True)

print("\nAggregated station-hour rows:", len(hourly))

print("\nDate range:")
print(hourly["transit_timestamp"].min())
print(hourly["transit_timestamp"].max())

print("\nUnique stations:")
print(hourly["station_complex_id"].nunique())

print("\nSample:")
print(hourly.head(20))

hourly.to_csv(
    output_path,
    index=False
)

print(
    f"\nSaved to: {output_path}"
)