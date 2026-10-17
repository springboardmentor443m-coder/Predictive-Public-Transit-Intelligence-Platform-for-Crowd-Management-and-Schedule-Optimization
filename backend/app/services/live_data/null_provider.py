from datetime import datetime, timezone
from typing import List
from app.schemas.live_data import VehiclePosition, ServiceAlert, TripUpdate, LiveFeedStatus, DataState
from app.services.live_data.base import LiveDataProvider, LiveDataNotConfiguredError


class UnconfiguredLiveDataProvider(LiveDataProvider):
    """
    Default placeholder implementation of LiveDataProvider for Module 1.
    
    Ensures no fake live data is passed off as real transportation feeds.
    Throws LiveDataNotConfiguredError if live endpoints are invoked.
    """

    @property
    def provider_name(self) -> str:
        return "Unconfigured Live Feed (Pending Provider Integration)"

    def get_status(self) -> LiveFeedStatus:
        return LiveFeedStatus(
            provider_name=self.provider_name,
            is_connected=False,
            data_state=DataState.UNAVAILABLE,
            status_message="Live transportation data is currently unavailable. Configure MTA GTFS-RT feed settings.",
            last_sync=None
        )

    async def fetch_vehicle_positions(self) -> List[VehiclePosition]:
        raise LiveDataNotConfiguredError(
            "Live transportation data is currently unavailable. "
            "Please configure GTFS-RT endpoint in environment settings."
        )

    async def fetch_service_alerts(self) -> List[ServiceAlert]:
        raise LiveDataNotConfiguredError(
            "Live transportation data is currently unavailable."
        )

    async def fetch_trip_updates(self) -> List[TripUpdate]:
        raise LiveDataNotConfiguredError(
            "Live transportation data is currently unavailable."
        )
