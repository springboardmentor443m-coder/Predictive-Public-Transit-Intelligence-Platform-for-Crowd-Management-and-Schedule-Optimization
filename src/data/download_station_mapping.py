import requests
import pandas as pd

URL = "https://data.ny.gov/resource/i9wp-a4ja.json"

params = {
    "$limit": 50000
}

response = requests.get(URL, params=params)
response.raise_for_status()

data = response.json()

df = pd.DataFrame(data)

print("Rows downloaded:", len(df))

columns = [
    "complex_id",
    "station_id",
    "gtfs_stop_id",
    "stop_name",
    "constituent_station_name",
    "borough",
    "daytime_routes",
]

df = df[columns].copy()

df["complex_id"] = pd.to_numeric(df["complex_id"], errors="coerce")
df["station_id"] = pd.to_numeric(df["station_id"], errors="coerce")

df = df.dropna(
    subset=[
        "complex_id",
        "station_id",
        "gtfs_stop_id"
    ]
)

df["complex_id"] = df["complex_id"].astype("int64")
df["station_id"] = df["station_id"].astype("int64")

mapping = df.drop_duplicates(
    subset=["complex_id", "gtfs_stop_id"]
)

print("Unique station mappings:", len(mapping))

print("\nSample:")
print(mapping.head(20))

output_path = "data/processed/station_mapping.csv"

mapping.to_csv(output_path, index=False)

print(f"\nSaved to: {output_path}")