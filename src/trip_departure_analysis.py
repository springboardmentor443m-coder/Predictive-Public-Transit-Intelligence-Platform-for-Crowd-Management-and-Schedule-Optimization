import pandas as pd

print("Building robust trip departure dataset...")

first_stops = {}

for chunk in pd.read_csv(
    "data/static/stop_times.txt",
    usecols=["trip_id", "departure_time", "stop_sequence"],
    dtype={
        "trip_id": "string",
        "departure_time": "string"
    },
    chunksize=100000
):

    chunk["stop_sequence"] = pd.to_numeric(
        chunk["stop_sequence"],
        errors="coerce"
    )

    chunk = chunk.sort_values(
        ["trip_id", "stop_sequence"]
    )

    chunk = chunk.drop_duplicates(
        "trip_id",
        keep="first"
    )

    for row in chunk.itertuples(index=False):
        trip_id = row.trip_id

        if (
            trip_id not in first_stops
            or row.stop_sequence < first_stops[trip_id][0]
        ):
            first_stops[trip_id] = (
                row.stop_sequence,
                row.departure_time
            )

print("Trips identified:", len(first_stops))

hours = {}

for stop_sequence, departure_time in first_stops.values():

    hour = departure_time.split(":")[0]

    hours[hour] = hours.get(hour, 0) + 1

result = pd.DataFrame(
    list(hours.items()),
    columns=["hour", "scheduled_trips"]
)

result["hour"] = pd.to_numeric(
    result["hour"],
    errors="coerce"
)

result = result.sort_values("hour")

print("\nRobust scheduled trips by departure hour:\n")
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
