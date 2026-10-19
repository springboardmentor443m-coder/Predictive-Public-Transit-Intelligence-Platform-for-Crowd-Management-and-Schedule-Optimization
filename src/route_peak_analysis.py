import pandas as pd

print("Loading trip-to-route mapping...")

trips = pd.read_csv(
    "data/static/trips.txt",
    usecols=["trip_id", "route_id"],
    dtype="string"
)

print("Trips loaded:", len(trips))

print("Reading stop_times in chunks...")

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

print("Trip departures identified:", len(first_stops))

departures = []

for trip_id, (_, departure_time) in first_stops.items():

    departures.append({
        "trip_id": trip_id,
        "departure_hour": int(
            departure_time.split(":")[0]
        )
    })

departures = pd.DataFrame(departures)

data = departures.merge(
    trips,
    on="trip_id",
    how="left"
)

route_hour = (
    data
    .groupby(
        ["route_id", "departure_hour"]
    )
    .size()
    .reset_index(
        name="scheduled_trips"
    )
)

peak = (
    route_hour
    .sort_values(
        ["route_id", "scheduled_trips"],
        ascending=[True, False]
    )
    .drop_duplicates(
        "route_id"
    )
)

routes = pd.read_csv(
    "data/static/routes.txt",
    usecols=[
        "route_id",
        "route_short_name",
        "route_long_name"
    ],
    dtype="string"
)

peak = peak.merge(
    routes,
    on="route_id",
    how="left"
)

peak = peak.sort_values(
    "scheduled_trips",
    ascending=False
)

print("\nPeak scheduled departure hour by route:\n")

print(
    peak[
        [
            "route_short_name",
            "departure_hour",
            "scheduled_trips",
            "route_long_name"
        ]
    ].to_string(index=False)
)

print("\nAnalysis completed successfully!")
