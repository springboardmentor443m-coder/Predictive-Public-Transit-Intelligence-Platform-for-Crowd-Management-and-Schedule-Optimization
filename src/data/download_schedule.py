import requests
import pandas as pd

URL = "https://data.ny.gov/resource/q9nv-uegs.json"

params = {
    "$limit": 500000,
    "$where": (
        "service_date >= '2025-05-05T00:00:00' "
        "AND service_date < '2025-05-06T00:00:00'"
    )
}

response = requests.get(URL, params=params)
response.raise_for_status()

data = response.json()

df = pd.DataFrame(data)

print("Rows downloaded:", len(df))

if not df.empty:
    print("\nService date:")
    print(df["service_date"].min())
    print(df["service_date"].max())

    print("\nDeparture time range:")
    print(df["departure_time"].min())
    print(df["departure_time"].max())

    print("\nUnique trains:", df["train_id"].nunique())
    print("Unique GTFS stops:", df["gtfs_stop_id"].nunique())
    print("Unique lines:", df["line"].nunique())

    output_path = "data/raw/mta_schedule_2025_05_05.csv"

    df.to_csv(output_path, index=False)

    print(f"\nSaved to: {output_path}")
else:
    print("No data returned.")