import pandas as pd

df = pd.read_csv("data/processed/station_hourly_ridership.csv")

print("Total passenger entries:", df["passenger_entries"].sum())
print("Average hourly entries:", df["passenger_entries"].mean())
print("Maximum hourly entries:", df["passenger_entries"].max())

print("\nTop 10 stations:")
top_stations = (
    df.groupby("station_complex")["passenger_entries"]
    .sum()
    .sort_values(ascending=False)
    .head(10)
)

print(top_stations)

print("\nRecords by borough:")
print(
    df.groupby("borough")["passenger_entries"]
    .sum()
    .sort_values(ascending=False)
)