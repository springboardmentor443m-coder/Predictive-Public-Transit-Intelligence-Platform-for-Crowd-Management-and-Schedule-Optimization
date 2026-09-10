import requests
import pandas as pd
import time

URL = "https://data.ny.gov/resource/y2qv-fytt.json"

start_time = "2025-05-05T00:00:00"
end_time = "2025-05-06T00:00:00"

batch_size = 100000
offset = 0

all_data = []

while True:

    params = {
        "$limit": batch_size,
        "$offset": offset,
        "$where": (
            f"timestamp >= '{start_time}' "
            f"AND timestamp < '{end_time}'"
        )
    }

    print(f"Downloading rows {offset} to {offset + batch_size}...")

    response = requests.get(URL, params=params)
    response.raise_for_status()

    data = response.json()

    if not data:
        break

    all_data.extend(data)

    print(f"Received: {len(data)} rows")

    if len(data) < batch_size:
        break

    offset += batch_size

    time.sleep(0.5)

print("\nTotal rows downloaded:", len(all_data))

df = pd.DataFrame(all_data)

if not df.empty:

    print("\nDate range:")
    print(df["timestamp"].min())
    print(df["timestamp"].max())

    print("\nUnique origin stations:")
    print(df["origin_station_complex_id"].nunique())

    print("\nUnique destination stations:")
    print(df["destination_station_complex_id"].nunique())

    output_path = "data/raw/mta_od_2025_05_05.csv"

    df.to_csv(output_path, index=False)

    print(f"\nSaved to: {output_path}")

else:
    print("No data returned.")