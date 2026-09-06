import pandas as pd

stops = pd.read_csv("data/static/stops.txt")
trips = pd.read_csv("data/static/trips.txt")
stop_times = pd.read_csv("data/static/stop_times.txt", nrows=1000)

print("GTFS files loaded successfully!")

print("Number of stops:", len(stops))
print("Number of trips:", len(trips))
print("Sample stop times loaded:", len(stop_times))

print("\nStops:")
print(stops.head())

print("\nTrips:")
print(trips.head())

print("\nStop times sample:")
print(stop_times.head())

print("\nDataset columns:")
print("Stops:", list(stops.columns))
print("Trips:", list(trips.columns))
print("Stop times:", list(stop_times.columns))

print("\nSample sizes:")
print("Stops:", stops.shape)
print("Trips:", trips.shape)
print("Stop times:", stop_times.shape)
