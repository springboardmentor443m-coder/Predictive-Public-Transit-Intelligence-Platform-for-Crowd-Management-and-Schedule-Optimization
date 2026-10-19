import pandas as pd

print("Analyzing scheduled departure times...")

hour_counts = {}

for chunk in pd.read_csv(
    "data/static/stop_times.txt",
    usecols=["departure_time"],
    dtype={"departure_time": "string"},
    chunksize=100000
):
    hours = (
        chunk["departure_time"]
        .str.split(":")
        .str[0]
    )

    counts = hours.value_counts()

    for hour, count in counts.items():
        hour_counts[hour] = hour_counts.get(hour, 0) + count

result = pd.DataFrame(
    list(hour_counts.items()),
    columns=["hour", "scheduled_departures"]
)

result["hour"] = pd.to_numeric(
    result["hour"],
    errors="coerce"
)

result = result.sort_values("hour")

print("\nScheduled departures by hour:\n")
print(result.to_string(index=False))

print("\nPeak scheduled hour:")

peak = result.loc[
    result["scheduled_departures"].idxmax()
]

print(
    f"{int(peak['hour']):02d}:00 - "
    f"{int(peak['scheduled_departures'])} departures"
)

print("\nAnalysis completed successfully!")
