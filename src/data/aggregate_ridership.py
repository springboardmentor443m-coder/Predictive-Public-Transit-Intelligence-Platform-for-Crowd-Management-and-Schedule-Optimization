import pandas as pd

input_path = "data/processed/ridership_clean_2025_05_05.csv"
output_path = "data/processed/station_hourly_ridership_2025_05_05.csv"

df = pd.read_csv(input_path)

df["transit_timestamp"] = pd.to_datetime(
    df["transit_timestamp"]
)

hourly = (
    df.groupby(
        [
            "transit_timestamp",
            "station_complex_id",
            "station_complex",
            "borough",
            "latitude",
            "longitude"
        ],
        as_index=False
    )["ridership"]
    .sum()
)

hourly = hourly.rename(
    columns={
        "ridership": "passenger_entries"
    }
)

hourly = hourly.sort_values(
    ["transit_timestamp", "station_complex_id"]
).reset_index(drop=True)

print("Original rows:", len(df))
print("Aggregated rows:", len(hourly))

print("\nDate range:")
print(hourly["transit_timestamp"].min())
print(hourly["transit_timestamp"].max())

print("\nUnique stations:")
print(hourly["station_complex_id"].nunique())

print("\nSample:")
print(hourly.head(20))

hourly.to_csv(output_path, index=False)

print(f"\nSaved to: {output_path}")