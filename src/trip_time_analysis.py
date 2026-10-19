import pandas as pd

print("Analyzing unique scheduled trips by departure hour...")

trip_hours = {}

for chunk in pd.read_csv(
    "data/static/stop_times.txt",
    usecols=["trip_id", "departure_time"],
    dtype={"trip_id": "string", "departure_time": "string"},
    chunksize=100000
):
    chunk["hour"] = (
        chunk["departure_time"]
        .str.split(":")
        .str[0]
    )

    # Keep one departure time per trip.
    # The first stop represents the trip's scheduled departure.
    first_stops = (
        chunk
        .sort_values(["trip_id", "departure_time"])
        .drop_duplicates("trip_id")
    )

    for hour in first_stops["hour"]:
        trip_hours[hour] = trip_hours.get(hour, 0) + 1

result = pd.DataFrame(
    list(trip_hours.items()),
    columns=["hour", "scheduled_trips"]
)

result["hour"] = pd.to_numeric(
    result["hour"],
    errors="coerce"
)

result = result.sort_values("hour")

print("\nScheduled trips by departure hour:\n")
print(result.to_string(index=False))

peak = result.loc[
    result["scheduled_trips"].idxmax()
]

print("\nPeak scheduled departure hour:")

print(
    f"{int(peak['hour']):02d}:00 - "
    f"{int(peak['scheduled_trips'])} scheduled trips"
)

print("\nAnalysis completed successfully!")
