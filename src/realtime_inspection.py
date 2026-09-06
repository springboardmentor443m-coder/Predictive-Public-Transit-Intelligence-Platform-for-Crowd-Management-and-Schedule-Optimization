from google.transit import gtfs_realtime_pb2

feed = gtfs_realtime_pb2.FeedMessage()

with open("data/realtime/VehiclePositions.pb", "rb") as f:
    feed.ParseFromString(f.read())

print("Realtime feed loaded successfully!")
print("Total entities:", len(feed.entity))

vehicle_count = 0

for entity in feed.entity:
    if entity.HasField("vehicle"):
        vehicle_count += 1

print("Vehicle position records:", vehicle_count)

print("\nFeed header:")
print(feed.header)

print("\nFirst 5 vehicle records:")

shown = 0

for entity in feed.entity:
    if entity.HasField("vehicle"):
        vehicle = entity.vehicle

        print("\nVehicle ID:", vehicle.vehicle.id)

        if vehicle.HasField("trip"):
            print("Trip ID:", vehicle.trip.trip_id)
            print("Route ID:", vehicle.trip.route_id)

        if vehicle.HasField("position"):
            print("Latitude:", vehicle.position.latitude)
            print("Longitude:", vehicle.position.longitude)

        if vehicle.HasField("timestamp"):
            print("Timestamp:", vehicle.timestamp)

        shown += 1

        if shown >= 5:
            break

print("\nRealtime feed inspection completed successfully!")
