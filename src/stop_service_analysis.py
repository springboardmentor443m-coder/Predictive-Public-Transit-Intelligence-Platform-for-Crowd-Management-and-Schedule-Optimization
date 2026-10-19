import pandas as pd

print("Reading stop_times.txt in chunks...")

counts = {}

for chunk in pd.read_csv(
    "data/static/stop_times.txt",
    usecols=["stop_id"],
    dtype={"stop_id": "string"},
    chunksize=100000
):
    chunk_counts = chunk["stop_id"].value_counts()

    for stop_id, count in chunk_counts.items():
        counts[stop_id] = counts.get(stop_id, 0) + count

stops = pd.read_csv(
    "data/static/stops.txt",
    dtype={"stop_id": "string"}
)

result = stops[["stop_id", "stop_name"]].copy()

result["service_events"] = (
    result["stop_id"]
    .map(counts)
    .fillna(0)
    .astype(int)
)

result = result.sort_values(
    "service_events",
    ascending=False
)

print("\nTop 20 stops by scheduled service events:\n")
print(result.head(20).to_string(index=False))

print("\nStops with at least one scheduled service:",
      (result["service_events"] > 0).sum())

print("Total stop-time records counted:",
      sum(counts.values()))

print("\nAnalysis completed successfully!")
