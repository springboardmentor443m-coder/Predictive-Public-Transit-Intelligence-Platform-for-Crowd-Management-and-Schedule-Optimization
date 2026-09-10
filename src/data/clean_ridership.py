import pandas as pd

input_path = "data/raw/mta_ridership_2025_05_05.csv"
output_path = "data/processed/ridership_clean_2025_05_05.csv"

df = pd.read_csv(input_path)

print("Rows loaded:", len(df))

df["transit_timestamp"] = pd.to_datetime(
    df["transit_timestamp"],
    errors="coerce"
)

df["station_complex_id"] = pd.to_numeric(
    df["station_complex_id"],
    errors="coerce"
)

df["ridership"] = pd.to_numeric(
    df["ridership"],
    errors="coerce"
)

df["transfers"] = pd.to_numeric(
    df["transfers"],
    errors="coerce"
)

df["latitude"] = pd.to_numeric(
    df["latitude"],
    errors="coerce"
)

df["longitude"] = pd.to_numeric(
    df["longitude"],
    errors="coerce"
)

df = df.drop(columns=["georeference"], errors="ignore")

df = df.dropna(
    subset=[
        "transit_timestamp",
        "station_complex_id",
        "station_complex",
        "ridership"
    ]
)

df["station_complex_id"] = df["station_complex_id"].astype("int64")

print("Rows after cleaning:", len(df))

print("\nDate range:")
print(df["transit_timestamp"].min())
print(df["transit_timestamp"].max())

print("\nMissing values:")
print(df.isnull().sum())

df.to_csv(output_path, index=False)

print(f"\nSaved to: {output_path}")