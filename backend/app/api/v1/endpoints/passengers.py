from typing import List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
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
    Configure an external GTFS-Realtime (GTFS-RT) endpoint URL to ingest transit
    vehicle telemetry from supported agencies (e.g. MBTA, BART).
    """
    return await realtime_passenger_service.configure_gtfs_rt(config)


@router.get("/gtfs-rt-status", response_model=GtfsRtStatusResponse)
async def get_gtfs_rt_status():
    """
    Check the connection and synchronization status of the external GTFS-RT feed.
    """
    return realtime_passenger_service.gtfs_rt_status


class ReplayCursorRequest(BaseModel):
    date: str  # YYYY-MM-DD
    hour: int  # 0 to 23


@router.post("/replay-cursor")
async def set_replay_cursor(cursor: ReplayCursorRequest):
    """
    Sets the Historical Replay cursor to a specific date (August - September 2025) and hour (0-23).
    Replays genuine RTI observations for that exact time slot.
    """
    realtime_passenger_service.set_replay_time(cursor.date, cursor.hour)
    telemetry = await realtime_passenger_service.get_live_telemetry()
    return {
        "status": "SUCCESS",
        "mode": "HISTORICAL DATA REPLAY",
        "replay_date": realtime_passenger_service.replay_date,
        "replay_hour": realtime_passenger_service.replay_hour,
        "total_active_passengers": telemetry.total_active_passengers_in_transit,
        "system_inflow_ppm": telemetry.system_inflow_ppm,
        "system_outflow_ppm": telemetry.system_outflow_ppm,
    }


@router.get("/replay-cursor")
async def get_replay_cursor():
    """
    Gets the current historical replay time cursor and dataset parameters.
    """
    return {
        "mode": "HISTORICAL DATA REPLAY",
        "data_notice": "REAL BMRCL HISTORICAL DATA ONLY - NO SIMULATED TELEMETRY",
        "replay_date": realtime_passenger_service.replay_date,
        "replay_hour": realtime_passenger_service.replay_hour,
        "available_dates_range": "2025-08-01 to 2025-09-30",
        "available_hours": list(range(24))
    }

