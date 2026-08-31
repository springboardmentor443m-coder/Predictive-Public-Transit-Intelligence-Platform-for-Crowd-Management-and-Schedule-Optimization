import pandas as pd

stops = pd.read_csv("data/static/stops.txt")
trips = pd.read_csv("data/static/trips.txt")
stop_times = pd.read_csv("data/static/stop_times.txt")

print("GTFS files loaded successfully!")
print("Number of stops:", len(stops))
print("Number of trips:", len(trips))
print("Number of stop times:", len(stop_times))

print("\nStops:")
print(stops.head())

print("\nTrips:")
print(trips.head())

print("\nStop times:")
print(stop_times.head())

print("\nDataset information:")
print("Stops columns:", list(stops.columns))
print("Trips columns:", list(trips.columns))
print("Stop times columns:", list(stop_times.columns))
print("\nDataset sizes:")
print("Stops:", stops.shape)
print("Trips:", trips.shape)
print("Stop times:", stop_times.shape)