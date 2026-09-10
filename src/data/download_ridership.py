import requests
import pandas as pd

URL = "https://data.ny.gov/resource/5wq4-mkjj.json"

params = {
    "$limit": 500000,
    "$where": (
        "transit_timestamp >= '2025-05-05T00:00:00' "
        "AND transit_timestamp < '2025-05-06T00:00:00'"
    )
}

response = requests.get(URL, params=params)
response.raise_for_status()

data = response.json()
df = pd.DataFrame(data)

print("Rows downloaded:", len(df))

if not df.empty:
    print("\nDate range:")
    print(df["transit_timestamp"].min())
    print(df["transit_timestamp"].max())

    output_path = "data/raw/mta_ridership_2025_05_05.csv"
    df.to_csv(output_path, index=False)

    print(f"\nSaved to: {output_path}")
else:
    print("No data returned.")