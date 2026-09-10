import pandas as pd

input_path = "data/processed/metroflow_integrated_2025_05_05.csv"

df = pd.read_csv(input_path)

df["transit_timestamp"] = pd.to_datetime(
    df["transit_timestamp"],
    errors="coerce"
)

print("=" * 60)
print("METROFLOW FINAL DATA QUALITY REPORT")
print("=" * 60)


# --------------------------------------------------
# 1. Dataset size
# --------------------------------------------------

print("\n1. DATASET SIZE")

print("Rows:", len(df))
print("Columns:", len(df.columns))
print("Unique stations:", df["station_complex_id"].nunique())
print("Unique timestamps:", df["transit_timestamp"].nunique())


# --------------------------------------------------
# 2. Date coverage
# --------------------------------------------------

print("\n2. DATE COVERAGE")

print("Start:", df["transit_timestamp"].min())
print("End:", df["transit_timestamp"].max())

print(
    "Hours:",
    sorted(df["transit_timestamp"].dt.hour.unique())
)


# --------------------------------------------------
# 3. Missing values
# --------------------------------------------------

print("\n3. MISSING VALUES")

print(df.isnull().sum())


# --------------------------------------------------
# 4. Duplicate records
# --------------------------------------------------

print("\n4. DUPLICATES")

duplicates = df.duplicated(
    subset=[
        "transit_timestamp",
        "station_complex_id"
    ]
).sum()

print(
    "Duplicate station-hour records:",
    duplicates
)


# --------------------------------------------------
# 5. Passenger entries
# --------------------------------------------------

print("\n5. PASSENGER ENTRIES")

print(df["passenger_entries"].describe())

print(
    "Zero-entry records:",
    (df["passenger_entries"] == 0).sum()
)

print(
    "Negative-entry records:",
    (df["passenger_entries"] < 0).sum()
)


# --------------------------------------------------
# 6. Passenger exits
# --------------------------------------------------

print("\n6. PASSENGER EXITS")

print(df["passenger_exits"].describe())

print(
    "Available exit records:",
    df["exit_data_available"].sum()
)

print(
    "Missing exit records:",
    (df["exit_data_available"] == 0).sum()
)

print(
    "Negative exit records:",
    (df["passenger_exits"] < 0).sum()
)


# --------------------------------------------------
# 7. Scheduled trains
# --------------------------------------------------

print("\n7. SCHEDULED TRAINS")

print(df["scheduled_trains"].describe())

print(
    "Available schedule records:",
    df["schedule_data_available"].sum()
)

print(
    "Missing schedule records:",
    (df["schedule_data_available"] == 0).sum()
)

print(
    "Negative schedule records:",
    (df["scheduled_trains"] < 0).sum()
)


# --------------------------------------------------
# 8. Top stations by total entries
# --------------------------------------------------

print("\n8. TOP 10 STATIONS BY PASSENGER ENTRIES")

top_stations = (
    df.groupby(
        [
            "station_complex_id",
            "station_complex",
            "borough"
        ]
    )["passenger_entries"]
    .sum()
    .sort_values(ascending=False)
    .head(10)
)

print(top_stations)


# --------------------------------------------------
# 9. Peak hours
# --------------------------------------------------

print("\n9. HOURLY PASSENGER DEMAND")

hourly_demand = (
    df.groupby("hour")["passenger_entries"]
    .sum()
    .sort_values(ascending=False)
)

print(hourly_demand)


# --------------------------------------------------
# 10. Highest-demand station-hour
# --------------------------------------------------

print("\n10. HIGHEST DEMAND STATION-HOUR")

max_row = df.loc[
    df["passenger_entries"].idxmax()
]

print(max_row[
    [
        "transit_timestamp",
        "station_complex_id",
        "station_complex",
        "borough",
        "passenger_entries",
        "passenger_exits",
        "scheduled_trains"
    ]
])


# --------------------------------------------------
# 11. Data types
# --------------------------------------------------

print("\n11. DATA TYPES")

print(df.dtypes)


# --------------------------------------------------
# 12. Final verdict
# --------------------------------------------------

print("\n" + "=" * 60)
print("FINAL VERDICT")
print("=" * 60)

if (
    duplicates == 0
    and
    (df["passenger_entries"] < 0).sum() == 0
    and
    (df["passenger_exits"].dropna() < 0).sum() == 0
    and
    (df["scheduled_trains"].dropna() < 0).sum() == 0
):
    print("PASS: Dataset passed core quality checks.")
else:
    print("WARNING: Dataset requires further investigation.")