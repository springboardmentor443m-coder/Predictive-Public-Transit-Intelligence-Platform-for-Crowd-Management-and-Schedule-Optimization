import random
import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
import httpx

from app.ml.data_generator import STATION_METADATA, get_rush_hour_multiplier
from app.schemas.passenger_schema import (
    PassengerTapEvent,
    TrainCarLoad,
    TrainPassengerTelemetry,
    StationPassengerMetric,
    GtfsRtConfig,
    GtfsRtStatusResponse,
    RealtimePassengerStreamResponse,
)

logger = logging.getLogger("metroflow.passenger_service")


class RealtimePassengerService:
    def __init__(self):
        self.tap_events_buffer: List[PassengerTapEvent] = []
        self.buffer_max_size: int = 150
        
        # GTFS-RT External Connector State
        self.gtfs_rt_config: Optional[GtfsRtConfig] = None
        self.gtfs_rt_status = GtfsRtStatusResponse(
            is_active=False,
            feed_url=None,
            provider_name="Simulated AFC/APC Real-Time Engine",
            last_polled=None,
            status_message="Operating on high-velocity local AFC/APC simulation engine. Ready for GTFS-RT link.",
            entities_ingested=0,
            sample_entities=[],
        )

        # Initial Active Trains
        self.trains_state: List[Dict[str, Any]] = [
            # Red Line Trains
            {"id": "TR-R101", "code": "RED-101", "line": "Red Line", "seq": 1, "dir": 1, "station_idx": 0, "speed": 52.0, "status": "IN_TRANSIT", "eta": 45},
            {"id": "TR-R102", "code": "RED-102", "line": "Red Line", "seq": 3, "dir": 1, "station_idx": 2, "speed": 48.0, "status": "BOARDING", "eta": 10},
            {"id": "TR-R103", "code": "RED-103", "line": "Red Line", "seq": 6, "dir": -1, "station_idx": 5, "speed": 55.0, "status": "IN_TRANSIT", "eta": 60},
            {"id": "TR-R104", "code": "RED-104", "line": "Red Line", "seq": 8, "dir": -1, "station_idx": 7, "speed": 0.0, "status": "AT_STATION", "eta": 0},
            # Blue Line Trains
            {"id": "TR-B201", "code": "BLU-201", "line": "Blue Line", "seq": 1, "dir": 1, "station_idx": 0, "speed": 46.0, "status": "BOARDING", "eta": 15},
            {"id": "TR-B202", "code": "BLU-202", "line": "Blue Line", "seq": 4, "dir": 1, "station_idx": 3, "speed": 58.0, "status": "IN_TRANSIT", "eta": 35},
            {"id": "TR-B203", "code": "BLU-203", "line": "Blue Line", "seq": 7, "dir": -1, "station_idx": 6, "speed": 50.0, "status": "IN_TRANSIT", "eta": 75},
            {"id": "TR-B204", "code": "BLU-204", "line": "Blue Line", "seq": 8, "dir": -1, "station_idx": 7, "speed": 0.0, "status": "AT_STATION", "eta": 0},
        ]

        # Initialize cars per train
        self.train_car_loads: Dict[str, List[int]] = {}
        for t in self.trains_state:
            # 4 cars per train, nominal capacity 250 each
            self.train_car_loads[t["id"]] = [
                random.randint(60, 180),
                random.randint(80, 210),
                random.randint(70, 200),
                random.randint(50, 170),
            ]

        # Populate initial buffer
        self._seed_initial_taps()

    def _seed_initial_taps(self):
        now = datetime.now(timezone.utc)
        categories = ["STANDARD", "STANDARD", "STANDARD", "COMMUTER_PASS", "COMMUTER_PASS", "STUDENT", "SENIOR"]
        
        for i in range(40):
            st = random.choice(STATION_METADATA)
            event_time = now - timedelta(seconds=random.randint(1, 180))
            event_type = random.choice(["TAP_IN", "TAP_OUT"])
            gate_num = random.randint(1, 8 if st["interchange"] else 4)
            card_id = f"CARD-{random.randint(1000, 9999)}"
            
            tap = PassengerTapEvent(
                event_id=f"EVT-{uuid.uuid4().hex[:8].upper()}",
                station_id=st["id"],
                station_code=st["code"],
                station_name=st["name"],
                line_name=st["line"],
                gate_id=f"GATE-{chr(65 + (st['id'] % 3))}{gate_num}",
                event_type=event_type,
                card_token=f"{card_id[:5]}****{card_id[-3:]}",
                fare_category=random.choice(categories),
                timestamp=event_time,
            )
            self.tap_events_buffer.append(tap)

        self.tap_events_buffer.sort(key=lambda x: x.timestamp, reverse=True)

    def _get_stations_for_line(self, line_name: str) -> List[dict]:
        return [s for s in STATION_METADATA if s["line"] == line_name]

    def _tick_train_simulation(self):
        """Advances trains along line sequences and simulates passenger boarding/alighting."""
        for t in self.trains_state:
            line_stations = self._get_stations_for_line(t["line"])
            max_idx = len(line_stations) - 1

            # Decrement ETA or move
            if t["status"] == "IN_TRANSIT":
                t["eta"] = max(0, t["eta"] - 4)
                if t["eta"] <= 5:
                    t["status"] = "BOARDING"
                    t["speed"] = 0.0
                    t["station_idx"] = (t["station_idx"] + t["dir"])
                    if t["station_idx"] >= max_idx:
                        t["station_idx"] = max_idx
                        t["dir"] = -1
                    elif t["station_idx"] <= 0:
                        t["station_idx"] = 0
                        t["dir"] = 1
            elif t["status"] == "BOARDING":
                # Alight and board passengers
                curr_loads = self.train_car_loads[t["id"]]
                curr_st = line_stations[t["station_idx"]]
                is_busy = curr_st["interchange"]
                alight_ratio = random.uniform(0.15, 0.40) if is_busy else random.uniform(0.05, 0.20)
                board_ratio = random.uniform(0.20, 0.50) if is_busy else random.uniform(0.08, 0.25)

                new_loads = []
                for car_passengers in curr_loads:
                    alighted = int(car_passengers * alight_ratio)
                    remaining = max(10, car_passengers - alighted)
                    boarded = int(random.randint(20, 80) * board_ratio)
                    new_count = min(250, remaining + boarded)
                    new_loads.append(new_count)

                self.train_car_loads[t["id"]] = new_loads
                t["status"] = "AT_STATION"
                t["eta"] = 0
            elif t["status"] == "AT_STATION":
                # Prepare to depart
                t["status"] = "IN_TRANSIT"
                t["speed"] = round(random.uniform(42.0, 62.0), 1)
                t["eta"] = random.randint(45, 90)

    def _generate_live_tap_events(self):
        """Generates realistic passenger gate tap-ins/tap-outs based on current rush hour."""
        now = datetime.now(timezone.utc)
        multiplier = get_rush_hour_multiplier(now.hour, now.minute, now.weekday() >= 5)
        
        # Number of taps to generate in this 2-3 second tick
        num_taps = random.randint(3, int(6 * max(1.0, multiplier)))
        categories = ["STANDARD", "STANDARD", "STANDARD", "COMMUTER_PASS", "COMMUTER_PASS", "STUDENT", "SENIOR"]

        for _ in range(num_taps):
            st = random.choice(STATION_METADATA)
            event_type = random.choices(["TAP_IN", "TAP_OUT"], weights=[0.55, 0.45])[0]
            gate_num = random.randint(1, 8 if st["interchange"] else 4)
            card_id = f"CARD-{random.randint(1000, 9999)}"

            tap = PassengerTapEvent(
                event_id=f"EVT-{uuid.uuid4().hex[:8].upper()}",
                station_id=st["id"],
                station_code=st["code"],
                station_name=st["name"],
                line_name=st["line"],
                gate_id=f"GATE-{chr(65 + (st['id'] % 3))}{gate_num}",
                event_type=event_type,
                card_token=f"{card_id[:5]}****{card_id[-3:]}",
                fare_category=random.choice(categories),
                timestamp=now,
            )
            self.tap_events_buffer.insert(0, tap)

        # Keep buffer within bounds
        if len(self.tap_events_buffer) > self.buffer_max_size:
            self.tap_events_buffer = self.tap_events_buffer[: self.buffer_max_size]

    async def get_live_telemetry(self) -> RealtimePassengerStreamResponse:
        """Called by background broadcaster and REST endpoints to return full live passenger stream."""
        now = datetime.now(timezone.utc)

        # Progress simulation tick
        self._tick_train_simulation()
        self._generate_live_tap_events()

        # Build Train Telemetry
        trains_response: List[TrainPassengerTelemetry] = []
        for t in self.trains_state:
            line_stations = self._get_stations_for_line(t["line"])
            curr_st = line_stations[t["station_idx"]]
            next_idx = min(len(line_stations) - 1, max(0, t["station_idx"] + t["dir"]))
            next_st = line_stations[next_idx]

            loads = self.train_car_loads[t["id"]]
            cars: List[TrainCarLoad] = []
            for i, count in enumerate(loads, start=1):
                pct = round((count / 250.0) * 100.0, 1)
                crowd = (
                    "CRUSH_LOAD" if pct >= 88.0
                    else "CROWDED" if pct >= 70.0
                    else "STANDING_ROOM" if pct >= 45.0
                    else "SEATS_AVAILABLE"
                )
                cars.append(
                    TrainCarLoad(
                        car_id=f"{t['code']}-C{i}",
                        car_number=i,
                        passenger_count=count,
                        max_capacity=250,
                        load_percentage=pct,
                        crowd_level=crowd,
                    )
                )

            total_passengers = sum(loads)
            overall_pct = round((total_passengers / 1000.0) * 100.0, 1)

            trains_response.append(
                TrainPassengerTelemetry(
                    train_id=t["id"],
                    train_code=t["code"],
                    line_name=t["line"],
                    current_station=curr_st["name"],
                    next_station=next_st["name"] if next_st["name"] != curr_st["name"] else "Terminus",
                    eta_seconds=t["eta"],
                    total_passengers=total_passengers,
                    total_capacity=1000,
                    overall_load_pct=overall_pct,
                    speed_kmh=t["speed"],
                    status=t["status"],
                    cars=cars,
                    last_updated=now,
                )
            )

        # Station Passenger Metrics (past minute window)
        one_min_ago = now - timedelta(seconds=60)
        recent_window_taps = [e for e in self.tap_events_buffer if e.timestamp >= one_min_ago]

        station_metrics: List[StationPassengerMetric] = []
        total_inflow = 0
        total_outflow = 0

        for st in STATION_METADATA:
            st_taps = [e for e in recent_window_taps if e.station_id == st["id"]]
            t_ins = sum(1 for e in st_taps if e.event_type == "TAP_IN")
            t_outs = sum(1 for e in st_taps if e.event_type == "TAP_OUT")
            
            # Scale slightly for realistic per-minute PPM
            t_ins_scaled = max(8, t_ins * 4 + (random.randint(15, 45) if st["interchange"] else random.randint(8, 20)))
            t_outs_scaled = max(6, t_outs * 4 + (random.randint(12, 40) if st["interchange"] else random.randint(6, 18)))
            net = t_ins_scaled - t_outs_scaled
            
            total_inflow += t_ins_scaled
            total_outflow += t_outs_scaled

            # Platform occupancy estimate
            current_occ = max(40, int(t_ins_scaled * 6 + st["capacity"] * 0.22))
            density_pct = (current_occ / st["capacity"]) * 100.0
            crowd_status = "CRITICAL" if density_pct >= 80 else ("MODERATE" if density_pct >= 55 else "NORMAL")

            station_metrics.append(
                StationPassengerMetric(
                    station_id=st["id"],
                    station_code=st["code"],
                    station_name=st["name"],
                    line_name=st["line"],
                    tap_ins_last_minute=t_ins_scaled,
                    tap_outs_last_minute=t_outs_scaled,
                    net_flux=net,
                    current_platform_passengers=current_occ,
                    crowd_status=crowd_status,
                )
            )

        total_active_transit = sum(t.total_passengers for t in trains_response)

        return RealtimePassengerStreamResponse(
            timestamp=now,
            system_inflow_ppm=total_inflow,
            system_outflow_ppm=total_outflow,
            net_passenger_flux=total_inflow - total_outflow,
            total_active_passengers_in_transit=total_active_transit,
            recent_tap_events=self.tap_events_buffer[:35],
            trains=trains_response,
            station_metrics=station_metrics,
            gtfs_rt_status=self.gtfs_rt_status,
        )

    async def configure_gtfs_rt(self, config: GtfsRtConfig) -> GtfsRtStatusResponse:
        """Sets external GTFS-RT feed URL and performs an initial validation poll."""
        self.gtfs_rt_config = config
        
        if not config.is_enabled or not config.feed_url:
            self.gtfs_rt_status = GtfsRtStatusResponse(
                is_active=False,
                feed_url=None,
                provider_name="Simulated AFC/APC Real-Time Engine",
                last_polled=datetime.now(timezone.utc),
                status_message="External GTFS-RT feed deactivated. Reverted to built-in high-velocity simulation engine.",
                entities_ingested=0,
                sample_entities=[],
            )
            return self.gtfs_rt_status

        # Attempt to poll the provided URL
        try:
            headers = {}
            if config.api_key:
                headers["Authorization"] = f"Bearer {config.api_key}"
                headers["x-api-key"] = config.api_key

            async with httpx.AsyncClient(timeout=8.0) as client:
                res = await client.get(config.feed_url, headers=headers)
                
            now = datetime.now(timezone.utc)
            if res.status_code == 200:
                # Try parsing JSON format
                entities = []
                try:
                    data = res.json()
                    if isinstance(data, dict):
                        entities = data.get("entity", data.get("vehicles", data.get("data", [])))
                    elif isinstance(data, list):
                        entities = data
                except Exception:
                    # Raw or protobuf response
                    entities = [{"raw_bytes": len(res.content), "content_type": res.headers.get("content-type")}]

                self.gtfs_rt_status = GtfsRtStatusResponse(
                    is_active=True,
                    feed_url=config.feed_url,
                    provider_name=config.provider_name or "Custom GTFS-RT Provider",
                    last_polled=now,
                    status_message=f"Connected successfully to GTFS-RT feed ({len(entities)} entities received).",
                    entities_ingested=len(entities),
                    sample_entities=entities[:5] if isinstance(entities, list) else [],
                )
            else:
                self.gtfs_rt_status = GtfsRtStatusResponse(
                    is_active=False,
                    feed_url=config.feed_url,
                    provider_name=config.provider_name or "Custom GTFS-RT Provider",
                    last_polled=now,
                    status_message=f"HTTP {res.status_code} received from GTFS-RT feed. Falling back to simulated AFC/APC.",
                    entities_ingested=0,
                    sample_entities=[],
                )
        except Exception as e:
            logger.warning(f"Failed to fetch external GTFS-RT feed: {e}")
            self.gtfs_rt_status = GtfsRtStatusResponse(
                is_active=False,
                feed_url=config.feed_url,
                provider_name=config.provider_name or "Custom GTFS-RT Provider",
                last_polled=datetime.now(timezone.utc),
                status_message=f"Network error connecting to GTFS-RT feed: {str(e)[:120]}. Falling back to internal engine.",
                entities_ingested=0,
                sample_entities=[],
            )

        return self.gtfs_rt_status


realtime_passenger_service = RealtimePassengerService()
