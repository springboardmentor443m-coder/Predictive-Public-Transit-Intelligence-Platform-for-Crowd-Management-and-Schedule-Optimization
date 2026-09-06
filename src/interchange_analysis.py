import pandas as pd

print("Loading trips...")

trips = pd.read_csv(
    "data/static/trips.txt",
    usecols=["trip_id", "route_id"],
    dtype="string"
)

print("Trips loaded:", len(trips))

print("Reading stop_times in chunks...")

route_stop_pairs = []

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

    route_stop_pairs.append(
        merged[["route_id", "stop_id"]].drop_duplicates()
    )

route_stop_pairs = pd.concat(route_stop_pairs)

route_stop_pairs = route_stop_pairs.drop_duplicates()

print("Unique route-stop relationships:",
      len(route_stop_pairs))

stops = pd.read_csv(
    "data/static/stops.txt",
    usecols=["stop_id", "stop_name"],
    dtype={"stop_id": "string"}
)

routes = pd.read_csv(
    "data/static/routes.txt",
    usecols=["route_id", "route_short_name"],
    dtype={"route_id": "string"}
)

result = (
    route_stop_pairs
    .groupby("stop_id")["route_id"]
    .nunique()
    .reset_index(name="route_count")
)

result = result.merge(
    stops,
    on="stop_id",
    how="left"
)

result = result.sort_values(
    ["route_count", "stop_name"],
    ascending=[False, True]
)

print("\nStations served by the most distinct routes:\n")

print(
    result.head(30).to_string(index=False)
)

print("\nAnalysis completed successfully!")
