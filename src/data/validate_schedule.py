import pandas as pd

input_path = "data/processed/station_hourly_schedule_2025_05_05.csv"

df = pd.read_csv(input_path)

df["transit_timestamp"] = pd.to_datetime(
    df["transit_timestamp"],
    errors="coerce"
)

print("Total rows:", len(df))

print("\nUnique stations:")
print(df["station_complex_id"].nunique())

print("\nUnique timestamps:")
print(df["transit_timestamp"].nunique())

print("\nDate range:")
print(df["transit_timestamp"].min())
print(df["transit_timestamp"].max())

print("\nHours present:")
print(sorted(df["transit_timestamp"].dt.hour.unique()))

print("\nDuplicate station-hour records:")

duplicates = df.duplicated(
    subset=[
        "transit_timestamp",
        "station_complex_id"
    ]
).sum()

print(duplicates)

print("\nScheduled train statistics:")
print(df["scheduled_trains"].describe())

print("\nRows per hour:")
print(
    df.groupby(
        df["transit_timestamp"].dt.hour
    ).size()
)

print("\nMissing values:")
print(df.isnull().sum())

print("\nSample:")
print(df.head(20))