import pytest
from google.transit import gtfs_realtime_pb2
from app.services.live_data.mta_subway import MTASubwayLiveDataProvider
from app.schemas.live_data import DataState


def create_sample_gtfs_protobuf() -> bytes:
    feed = gtfs_realtime_pb2.FeedMessage()
    feed.header.gtfs_realtime_version = "2.0"
    feed.header.timestamp = 1790273309

    # Add VehiclePosition Entity
    e1 = feed.entity.add()
    e1.id = "v-entity-1"
    e1.vehicle.trip.trip_id = "010000_1..N"
    e1.vehicle.trip.route_id = "1"
    e1.vehicle.position.latitude = 40.7580
    e1.vehicle.position.longitude = -73.9855
    e1.vehicle.current_status = gtfs_realtime_pb2.VehiclePosition.VehicleStopStatus.IN_TRANSIT_TO
    e1.vehicle.stop_id = "127N"
    e1.vehicle.timestamp = 1790273309

    # Add TripUpdate Entity
    e2 = feed.entity.add()
    e2.id = "tu-entity-2"
    e2.trip_update.trip.trip_id = "020000_2..S"
    e2.trip_update.trip.route_id = "2"
    stu = e2.trip_update.stop_time_update.add()
    stu.stop_id = "228S"
    stu.arrival.delay = 180

    return feed.SerializeToString()


def test_mta_provider_parse_protobuf():
    provider = MTASubwayLiveDataProvider()
    pb_bytes = create_sample_gtfs_protobuf()

    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(pb_bytes)

    assert feed.header.timestamp == 1790273309
    assert len(feed.entity) == 2
    assert feed.entity[0].vehicle.trip.route_id == "1"
    assert feed.entity[1].trip_update.stop_time_update[0].arrival.delay == 180
