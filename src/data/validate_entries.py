import pandas as pd

input_path = "data/processed/station_hourly_ridership_2025_05_05.csv"

df = pd.read_csv(input_path)

df["transit_timestamp"] = pd.to_datetime(
    df["transit_timestamp"],
    errors="coerce"
)

print("Total rows:", len(df))

print("\nUnique stations:", df["station_complex_id"].nunique())

print("\nUnique timestamps:", df["transit_timestamp"].nunique())

print("\nHours present:")
print(
    sorted(
        df["transit_timestamp"].dt.hour.unique()
    )
)

print("\nRows per hour:")
print(
    df.groupby(
        df["transit_timestamp"].dt.hour
    ).size()
)

print("\nDuplicate station-hour records:")

duplicates = df.duplicated(
    subset=[
        "transit_timestamp",
        "station_complex_id"
    ]
).sum()

print(duplicates)

print("\nEntry statistics:")
print(
    df["passenger_entries"].describe()
)

print("\nSample timestamps:")
print(
    df["transit_timestamp"]
    .drop_duplicates()
    .sort_values()
)