import pandas as pd

input_path = "data/raw/mta_od_2025_05_05.csv"
output_path = "data/processed/station_hourly_exits_2025_05_05.csv"

df = pd.read_csv(input_path)

print("Rows loaded:", len(df))

# Convert required columns
df["timestamp"] = pd.to_datetime(
    df["timestamp"],
    errors="coerce"
)

df["destination_station_complex_id"] = pd.to_numeric(
    df["destination_station_complex_id"],
    errors="coerce"
)

df["estimated_average_ridership"] = pd.to_numeric(
    df["estimated_average_ridership"],
    errors="coerce"
)

# Remove invalid records
df = df.dropna(
    subset=[
        "timestamp",
        "destination_station_complex_id",
        "destination_station_complex_name",
        "estimated_average_ridership"
    ]
)

df["destination_station_complex_id"] = (
    df["destination_station_complex_id"].astype("int64")
)

print("Rows after cleaning:", len(df))

# Aggregate destination flows to station-hour level
exits = (
    df.groupby(
        [
            "timestamp",
            "destination_station_complex_id",
            "destination_station_complex_name"
        ],
        as_index=False
    )["estimated_average_ridership"]
    .sum()
)

# Rename columns
exits = exits.rename(
    columns={
        "destination_station_complex_id": "station_complex_id",
        "destination_station_complex_name": "station_complex",
        "estimated_average_ridership": "passenger_exits"
    }
)

# Sort
exits = exits.sort_values(
    ["timestamp", "station_complex_id"]
).reset_index(drop=True)

print("\nAggregated station-hour exit rows:", len(exits))

print("\nDate range:")
print(exits["timestamp"].min())
print(exits["timestamp"].max())

print("\nUnique stations:")
print(exits["station_complex_id"].nunique())

print("\nSample:")
print(exits.head(20))

# Save
exits.to_csv(output_path, index=False)

print(f"\nSaved to: {output_path}")