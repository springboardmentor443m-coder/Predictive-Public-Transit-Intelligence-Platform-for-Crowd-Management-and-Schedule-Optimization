from typing import List
from fastapi import APIRouter, HTTPException, Depends
from app.services.realtime_passenger_service import realtime_passenger_service
from app.schemas.passenger_schema import (
    RealtimePassengerStreamResponse,
    TrainPassengerTelemetry,
    StationPassengerMetric,
    GtfsRtConfig,
    GtfsRtStatusResponse,
)

router = APIRouter()


@router.get("/live-stream", response_model=RealtimePassengerStreamResponse)
async def get_live_passenger_stream():
    """
    Get full real-time passenger telemetry snapshot including recent AFC card taps,
    live train car-level passenger loads (APC), station platform metrics, and GTFS-RT connector status.
    """
    return await realtime_passenger_service.get_live_telemetry()


@router.get("/train-telemetry", response_model=List[TrainPassengerTelemetry])
async def get_live_train_telemetry():
    """
    Get current Automated Passenger Counter (APC) loads for all active trains and individual cars.
    """
    telemetry = await realtime_passenger_service.get_live_telemetry()
    return telemetry.trains


@router.get("/station-metrics", response_model=List[StationPassengerMetric])
async def get_station_passenger_metrics():
    """
    Get real-time tap-in/tap-out rates and net passenger influx for every transit station.
    """
    telemetry = await realtime_passenger_service.get_live_telemetry()
    return telemetry.station_metrics


@router.post("/gtfs-rt-config", response_model=GtfsRtStatusResponse)
async def configure_gtfs_rt_feed(config: GtfsRtConfig):
    """
    Configure an external GTFS-Realtime (GTFS-RT) endpoint URL to ingest real-world
    passenger telemetry from agencies (e.g. MTA, TfL, MBTA, BART).
    """
    return await realtime_passenger_service.configure_gtfs_rt(config)


@router.get("/gtfs-rt-status", response_model=GtfsRtStatusResponse)
async def get_gtfs_rt_status():
    """
    Check the connection and synchronization status of the external GTFS-RT feed.
    """
    return realtime_passenger_service.gtfs_rt_status
