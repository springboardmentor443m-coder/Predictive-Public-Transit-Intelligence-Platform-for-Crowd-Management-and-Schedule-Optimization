import pandas as pd

input_path = "data/processed/station_hourly_exits_2025_05_05.csv"

df = pd.read_csv(input_path)

df["timestamp"] = pd.to_datetime(
    df["timestamp"],
    errors="coerce"
)

print("Total rows:", len(df))

print("\nUnique stations:", df["station_complex_id"].nunique())

print("\nUnique timestamps:", df["timestamp"].nunique())

print("\nHours present:")
print(sorted(df["timestamp"].dt.hour.unique()))

print("\nRows per hour:")
print(
    df.groupby(df["timestamp"].dt.hour)
    .size()
)

print("\nDuplicate station-hour records:")

duplicates = df.duplicated(
    subset=["timestamp", "station_complex_id"]
).sum()

print(duplicates)

print("\nExit statistics:")
print(df["passenger_exits"].describe())

print("\nSample timestamps:")
print(
    df["timestamp"]
    .drop_duplicates()
    .sort_values()
    .head(30)
)