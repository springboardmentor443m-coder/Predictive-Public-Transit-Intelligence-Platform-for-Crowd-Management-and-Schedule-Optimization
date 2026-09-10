import pandas as pd

entries_path = "data/processed/station_hourly_ridership_2025_05_05.csv"
exits_path = "data/processed/station_hourly_exits_2025_05_05.csv"
schedule_path = "data/processed/station_hourly_schedule_2025_05_05.csv"

output_path = "data/processed/metroflow_integrated_2025_05_05.csv"


# --------------------------------------------------
# 1. Load datasets
# --------------------------------------------------

entries = pd.read_csv(entries_path)
exits = pd.read_csv(exits_path)
schedule = pd.read_csv(schedule_path)

print("Entries rows:", len(entries))
print("Exits rows:", len(exits))
print("Schedule rows:", len(schedule))


# --------------------------------------------------
# 2. Convert timestamps
# --------------------------------------------------

entries["transit_timestamp"] = pd.to_datetime(
    entries["transit_timestamp"],
    errors="coerce"
)

exits["timestamp"] = pd.to_datetime(
    exits["timestamp"],
    errors="coerce"
)

schedule["transit_timestamp"] = pd.to_datetime(
    schedule["transit_timestamp"],
    errors="coerce"
)


# --------------------------------------------------
# 3. Keep common date window
# --------------------------------------------------

start_time = pd.Timestamp("2025-05-05 00:00:00")
end_time = pd.Timestamp("2025-05-06 00:00:00")

entries = entries[
    (entries["transit_timestamp"] >= start_time)
    & (entries["transit_timestamp"] < end_time)
].copy()

exits = exits[
    (exits["timestamp"] >= start_time)
    & (exits["timestamp"] < end_time)
].copy()

schedule = schedule[
    (schedule["transit_timestamp"] >= start_time)
    & (schedule["transit_timestamp"] < end_time)
].copy()


# --------------------------------------------------
# 4. Prepare exits
# --------------------------------------------------

exits = exits.rename(
    columns={
        "timestamp": "transit_timestamp"
    }
)

exits = exits[
    [
        "transit_timestamp",
        "station_complex_id",
        "passenger_exits"
    ]
].copy()


# --------------------------------------------------
# 5. Prepare schedule
# --------------------------------------------------

schedule = schedule[
    [
        "transit_timestamp",
        "station_complex_id",
        "scheduled_trains"
    ]
].copy()


# --------------------------------------------------
# 6. Merge entries + exits
# --------------------------------------------------

integrated = entries.merge(
    exits,
    on=[
        "transit_timestamp",
        "station_complex_id"
    ],
    how="left"
)

# Flag whether an exit observation exists
integrated["exit_data_available"] = (
    integrated["passenger_exits"].notna()
).astype(int)


# --------------------------------------------------
# 7. Merge schedule
# --------------------------------------------------

integrated = integrated.merge(
    schedule,
    on=[
        "transit_timestamp",
        "station_complex_id"
    ],
    how="left"
)

# Flag whether schedule observation exists
integrated["schedule_data_available"] = (
    integrated["scheduled_trains"].notna()
).astype(int)


# --------------------------------------------------
# 8. Add time features
# --------------------------------------------------

integrated["hour"] = (
    integrated["transit_timestamp"].dt.hour
)

integrated["day_of_week"] = (
    integrated["transit_timestamp"].dt.dayofweek
)

integrated["is_weekend"] = (
    integrated["day_of_week"] >= 5
).astype(int)


# --------------------------------------------------
# 9. Sort
# --------------------------------------------------

integrated = integrated.sort_values(
    [
        "transit_timestamp",
        "station_complex_id"
    ]
).reset_index(drop=True)


# --------------------------------------------------
# 10. Validation
# --------------------------------------------------

print("\nFinal integrated rows:", len(integrated))

print(
    "Unique stations:",
    integrated["station_complex_id"].nunique()
)

print(
    "Unique timestamps:",
    integrated["transit_timestamp"].nunique()
)

print("\nDate range:")
print(integrated["transit_timestamp"].min())
print(integrated["transit_timestamp"].max())

print("\nMissing values:")
print(integrated.isnull().sum())

print("\nData availability:")

print(
    "Exit data available:",
    integrated["exit_data_available"].sum()
)

print(
    "Exit data missing:",
    (integrated["exit_data_available"] == 0).sum()
)

print(
    "Schedule data available:",
    integrated["schedule_data_available"].sum()
)

print(
    "Schedule data missing:",
    (integrated["schedule_data_available"] == 0).sum()
)

duplicates = integrated.duplicated(
    subset=[
        "transit_timestamp",
        "station_complex_id"
    ]
).sum()

print(
    "\nDuplicate station-hour records:",
    duplicates
)

print("\nColumns:")
print(integrated.columns.tolist())


# --------------------------------------------------
# 11. Save
# --------------------------------------------------

integrated.to_csv(
    output_path,
    index=False
)

print(
    f"\nSaved to: {output_path}"
)