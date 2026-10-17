import time
import logging
from datetime import datetime, timezone
from typing import List, Dict, Tuple, Optional
import urllib.request
import urllib.error
from google.transit import gtfs_realtime_pb2

from app.services.live_data.base import LiveDataProvider, LiveDataNotConfiguredError
from app.schemas.live_data import VehiclePosition, ServiceAlert, TripUpdate, LiveFeedStatus, DataState
from app.schemas.live_mta import TransitVehicleState, NormalizedTripUpdate, NormalizedServiceAlert
from app.models.feed_status import HealthStatus
from app.core.config import settings

logger = logging.getLogger("metroflow.mta")

# Official NYC MTA Subway GTFS-Realtime Endpoints
# No API key required — feeds are publicly available (confirmed Oct 2026)
# Source: https://api.mta.info/#/subwayRealTimeFeeds
MTA_SUBWAY_FEEDS = {
    "PRIMARY_1234567S": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs",
    "ACE_LINES":        "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-ace",
    "BDFM_LINES":       "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-bdfm",
    "G_LINE":           "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-g",
    "JZ_LINES":         "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-jz",
    "NQRW_LINES":       "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-nqrw",
    "L_LINE":           "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-l",
    "SIR_LINE":         "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-si",
}

MTA_ALERTS_FEED = "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/camsys%2Fsubway-alerts"


class MTASubwayLiveDataProvider(LiveDataProvider):
    """
    Official NYC MTA Subway GTFS-Realtime Live Data Provider.
    Parses live Protobuf streams and normalizes entities into MetroFlow internal models.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or getattr(settings, 'MTA_SUBWAY_API_KEY', None)
        self.last_sync_time: Optional[datetime] = None
        self.last_feed_timestamp: Optional[datetime] = None
        self.last_latency_ms: int = 0
        self.last_error: Optional[str] = None
        self.last_status: HealthStatus = HealthStatus.CONNECTING

    @property
    def provider_name(self) -> str:
        return "Official NYC MTA Subway GTFS-Realtime"

    def _get_headers(self) -> dict:
        headers = {"User-Agent": "MetroFlow/1.0 (Intelligent Metro Operations)"}
        if self.api_key:
            headers["x-api-key"] = self.api_key
        return headers

    def _fetch_protobuf_feed(self, url: str) -> Tuple[gtfs_realtime_pb2.FeedMessage, int]:
        req = urllib.request.Request(url, headers=self._get_headers())
        start_t = time.time()
        with urllib.request.urlopen(req, timeout=12) as response:
            data = response.read()
        latency_ms = int((time.time() - start_t) * 1000)
        
        feed = gtfs_realtime_pb2.FeedMessage()
        feed.ParseFromString(data)
        return feed, latency_ms

    def get_status(self) -> LiveFeedStatus:
        now = datetime.now(timezone.utc)
        is_connected = self.last_status in (HealthStatus.LIVE, HealthStatus.STALE)
        
        # Calculate staleness
        if self.last_sync_time:
            age_seconds = (now - self.last_sync_time).total_seconds()
            if age_seconds > 90 and self.last_status == HealthStatus.LIVE:
                self.last_status = HealthStatus.STALE

        status_msg = (
            f"Connected to MTA feeds. Latency: {self.last_latency_ms}ms"
            if is_connected
            else f"Feed status: {self.last_status.value}. Error: {self.last_error or 'None'}"
        )

        return LiveFeedStatus(
            provider_name=self.provider_name,
            is_connected=is_connected,
            data_state=DataState.LIVE,
            status_message=status_msg,
            last_sync=self.last_sync_time
        )

    async def fetch_vehicle_positions(self) -> List[VehiclePosition]:
        vehicles, _, _ = await self.fetch_all_normalized_entities()
        # Map to base schema
        result = []
        for v in vehicles:
            result.append(
                VehiclePosition(
                    vehicle_id=v.vehicle_id,
                    trip_id=v.trip_id,
                    route_id=v.route_id,
                    latitude=v.latitude,
                    longitude=v.longitude,
                    bearing=v.bearing,
                    current_stop_sequence=v.current_stop_sequence,
                    timestamp=v.timestamp,
                    data_state=DataState.LIVE
                )
            )
        return result

    async def fetch_service_alerts(self) -> List[ServiceAlert]:
        _, _, alerts = await self.fetch_all_normalized_entities()
        result = []
        for a in alerts:
            result.append(
                ServiceAlert(
                    alert_id=a.alert_id,
                    header_text=a.header_text,
                    description_text=a.description_text,
                    affected_routes=a.affected_routes,
                    affected_stations=a.affected_stops,
                    timestamp=a.timestamp,
                    data_state=DataState.LIVE
                )
            )
        return result

    async def fetch_trip_updates(self) -> List[TripUpdate]:
        _, trip_updates, _ = await self.fetch_all_normalized_entities()
        result = []
        for tu in trip_updates:
            result.append(
                TripUpdate(
                    trip_id=tu.trip_id,
                    route_id=tu.route_id,
                    delay_seconds=tu.delay_seconds,
                    stop_sequence=None,
                    next_station_id=tu.stop_id,
                    timestamp=tu.timestamp,
                    data_state=DataState.LIVE
                )
            )
        return result

    async def fetch_all_normalized_entities(
        self
    ) -> Tuple[List[TransitVehicleState], List[NormalizedTripUpdate], List[NormalizedServiceAlert]]:
        """Fetch all primary MTA Subway GTFS-RT feeds and return normalized internal models."""
        normalized_vehicles: List[TransitVehicleState] = []
        normalized_trips: List[NormalizedTripUpdate] = []
        normalized_alerts: List[NormalizedServiceAlert] = []

        total_latency = 0
        feed_count = 0
        feed_header_time: Optional[datetime] = None

        try:
            # Parse primary subway feeds
            for feed_key, feed_url in MTA_SUBWAY_FEEDS.items():
                try:
                    feed, latency = self._fetch_protobuf_feed(feed_url)
                    total_latency += latency
                    feed_count += 1

                    if feed.header.timestamp and not feed_header_time:
                        feed_header_time = datetime.fromtimestamp(feed.header.timestamp, tz=timezone.utc)

                    for entity in feed.entity:
                        now_utc = datetime.now(timezone.utc)

                        # Parse VehiclePositions
                        if entity.HasField("vehicle"):
                            v = entity.vehicle
                            v_id = v.vehicle.id if v.vehicle.id else f"mta-v-{v.trip.trip_id}"
                            
                            # Check coordinates availability
                            lat = float(v.position.latitude) if v.HasField("position") and v.position.latitude != 0.0 else None
                            lon = float(v.position.longitude) if v.HasField("position") and v.position.longitude != 0.0 else None
                            bearing = float(v.position.bearing) if v.HasField("position") and v.position.bearing else None

                            status_str = (
                                gtfs_realtime_pb2.VehiclePosition.VehicleStopStatus.Name(v.current_status)
                                if v.HasField("current_status")
                                else "IN_TRANSIT"
                            )

                            v_time = (
                                datetime.fromtimestamp(v.timestamp, tz=timezone.utc)
                                if v.timestamp
                                else now_utc
                            )

                            normalized_vehicles.append(
                                TransitVehicleState(
                                    vehicle_id=v_id,
                                    trip_id=v.trip.trip_id if v.HasField("trip") else None,
                                    route_id=v.trip.route_id if v.HasField("trip") and v.trip.route_id else "Subway",
                                    direction_id=v.trip.direction_id if v.HasField("trip") and v.trip.direction_id else 0,
                                    current_stop_id=v.stop_id if v.stop_id else None,
                                    current_stop_sequence=v.current_stop_sequence if v.HasField("current_stop_sequence") else None,
                                    current_status=status_str,
                                    latitude=lat,
                                    longitude=lon,
                                    bearing=bearing,
                                    passenger_count=None,  # Not provided by MTA live feed
                                    occupancy_rate=None,   # Not provided by MTA live feed
                                    timestamp=v_time,
                                    data_state=DataState.LIVE
                                )
                            )

                        # Parse TripUpdates
                        if entity.HasField("trip_update"):
                            tu = entity.trip_update
                            trip_id = tu.trip.trip_id
                            route_id = tu.trip.route_id if tu.trip.route_id else "Subway"
                            
                            tu_time = (
                                datetime.fromtimestamp(tu.timestamp, tz=timezone.utc)
                                if tu.timestamp
                                else now_utc
                            )

                            for stu in tu.stop_time_update:
                                arr_delay = stu.arrival.delay if stu.HasField("arrival") and stu.arrival.HasField("delay") else 0
                                arr_time = (
                                    datetime.fromtimestamp(stu.arrival.time, tz=timezone.utc)
                                    if stu.HasField("arrival") and stu.arrival.time
                                    else None
                                )
                                dep_time = (
                                    datetime.fromtimestamp(stu.departure.time, tz=timezone.utc)
                                    if stu.HasField("departure") and stu.departure.time
                                    else None
                                )

                                normalized_trips.append(
                                    NormalizedTripUpdate(
                                        trip_id=trip_id,
                                        route_id=route_id,
                                        stop_id=stu.stop_id,
                                        delay_seconds=arr_delay,
                                        estimated_arrival=arr_time,
                                        estimated_departure=dep_time,
                                        timestamp=tu_time,
                                        data_state=DataState.LIVE
                                    )
                                )
                except Exception as feed_err:
                    logger.warning(f"Error fetching MTA feed {feed_key}: {feed_err}")

            # Parse Service Alerts feed
            try:
                alert_feed, alert_lat = self._fetch_protobuf_feed(MTA_ALERTS_FEED)
                for entity in alert_feed.entity:
                    try:
                        if entity.HasField("alert"):
                            alt = entity.alert
                            header = (
                                alt.header_text.translation[0].text
                                if alt.HasField("header_text") and len(alt.header_text.translation) > 0
                                else "Service Notice"
                            )
                            desc = (
                                alt.description_text.translation[0].text
                                if alt.HasField("description_text") and len(alt.description_text.translation) > 0
                                else None
                            )
                            
                            routes = [ie.route_id for ie in alt.informed_entity if ie.route_id]
                            stops = [ie.stop_id for ie in alt.informed_entity if ie.stop_id]

                            start_t = (
                                datetime.fromtimestamp(alt.active_period[0].start, tz=timezone.utc)
                                if alt.active_period and alt.active_period[0].start
                                else None
                            )
                            end_t = (
                                datetime.fromtimestamp(alt.active_period[0].end, tz=timezone.utc)
                                if alt.active_period and alt.active_period[0].end
                                else None
                            )

                            normalized_alerts.append(
                                NormalizedServiceAlert(
                                    alert_id=entity.id,
                                    header_text=header,
                                    description_text=desc,
                                    affected_routes=routes,
                                    affected_stops=stops,
                                    start_time=start_t,
                                    end_time=end_t,
                                    active=True,
                                    timestamp=datetime.now(timezone.utc),
                                    data_state=DataState.LIVE
                                )
                            )
                    except Exception as entity_err:
                        logger.warning(f"Skipping malformed alert entity {entity.id}: {entity_err}")
            except Exception as alert_err:
                logger.warning(f"Error fetching MTA Alerts feed: {alert_err}")

            self.last_sync_time = datetime.now(timezone.utc)
            self.last_feed_timestamp = feed_header_time or self.last_sync_time
            self.last_latency_ms = int(total_latency / max(1, feed_count))
            self.last_status = HealthStatus.LIVE
            self.last_error = None

        except Exception as e:
            self.last_status = HealthStatus.ERROR
            self.last_error = str(e)
            logger.error(f"Critical failure fetching MTA GTFS-RT feeds: {e}")

        return normalized_vehicles, normalized_trips, normalized_alerts
