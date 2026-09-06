import pandas as pd

print("Loading trips...")

trips = pd.read_csv(
    "data/static/trips.txt",
    usecols=["trip_id", "route_id", "trip_headsign"],
    dtype="string"
)

print("Trips loaded:", len(trips))

print("Reading stop_times in chunks...")

results = []

for chunk in pd.read_csv(
    "data/static/stop_times.txt",
    usecols=["trip_id", "stop_id"],
    dtype="string",
    chunksize=100000
):
    merged = chunk.merge(
        trips,
        on="trip_id",
        how="left"
    )

    results.append(
        merged.groupby(
            ["route_id", "stop_id"]
        ).size().reset_index(name="service_events")
    )

route_stops = pd.concat(results)

route_stops = (
    route_stops
    .groupby(["route_id", "stop_id"])["service_events"]
    .sum()
    .reset_index()
)

stops = pd.read_csv(
    "data/static/stops.txt",
    usecols=["stop_id", "stop_name"],
    dtype={"stop_id": "string"}
)

routes = pd.read_csv(
    "data/static/routes.txt",
    usecols=["route_id", "route_short_name", "route_long_name"],
    dtype={"route_id": "string"}
)

route_stops = route_stops.merge(
    stops,
    on="stop_id",
    how="left"
)

route_stops = route_stops.merge(
    routes,
    on="route_id",
    how="left"
)

route_stops = route_stops.sort_values(
    "service_events",
    ascending=False
)

print("\nTop 30 route-stop service relationships:\n")

print(
    route_stops[
        [
            "route_short_name",
            "stop_name",
            "service_events"
        ]
    ].head(30).to_string(index=False)
)

print("\nAnalysis completed successfully!")
