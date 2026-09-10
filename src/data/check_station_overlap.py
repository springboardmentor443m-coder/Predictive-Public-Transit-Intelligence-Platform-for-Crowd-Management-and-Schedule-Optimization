import pandas as pd

entries_path = "data/processed/station_hourly_ridership_2025_05_05.csv"
exits_path = "data/processed/station_hourly_exits_2025_05_05.csv"
schedule_path = "data/processed/station_hourly_schedule_2025_05_05.csv"

entries = pd.read_csv(entries_path)
exits = pd.read_csv(exits_path)
schedule = pd.read_csv(schedule_path)

entry_stations = set(entries["station_complex_id"])
exit_stations = set(exits["station_complex_id"])
schedule_stations = set(schedule["station_complex_id"])

print("Entries stations:", len(entry_stations))
print("Exit stations:", len(exit_stations))
print("Schedule stations:", len(schedule_stations))

print("\n--- Pairwise overlap ---")

print(
    "Entries ∩ Exits:",
    len(entry_stations & exit_stations)
)

print(
    "Entries ∩ Schedule:",
    len(entry_stations & schedule_stations)
)

print(
    "Exits ∩ Schedule:",
    len(exit_stations & schedule_stations)
)

print("\n--- All three datasets ---")

common_stations = (
    entry_stations
    & exit_stations
    & schedule_stations
)

print(
    "Stations present in all 3:",
    len(common_stations)
)

print("\n--- Stations missing from each dataset ---")

print(
    "Entries missing from Exits:",
    len(entry_stations - exit_stations)
)

print(
    "Entries missing from Schedule:",
    len(entry_stations - schedule_stations)
)

print(
    "Exits missing from Entries:",
    len(exit_stations - entry_stations)
)

print(
    "Exits missing from Schedule:",
    len(exit_stations - schedule_stations)
)

print(
    "Schedule missing from Entries:",
    len(schedule_stations - entry_stations)
)

print(
    "Schedule missing from Exits:",
    len(schedule_stations - exit_stations)
)

print("\n--- Common station IDs ---")

print(
    sorted(common_stations)
)