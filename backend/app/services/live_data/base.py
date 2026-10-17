from abc import ABC, abstractmethod
from typing import List, Optional
from app.schemas.live_data import VehiclePosition, ServiceAlert, TripUpdate, LiveFeedStatus, DataState


class LiveDataNotConfiguredError(Exception):
    """Exception raised when attempting to access a live feed that is not configured or connected."""
    pass


class LiveDataProvider(ABC):
    """
    Abstract interface for MetroFlow transportation data feeds (GTFS-RT, SIRI, custom IoT, etc.).
    
    IMPORTANT: Implementations MUST explicitly label returned data with its DataState 
    (LIVE vs HISTORICAL vs PREDICTED vs UNAVAILABLE). Never fabricate live data.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name/Identifier of the data provider."""
        pass

    @abstractmethod
    def get_status(self) -> LiveFeedStatus:
        """Check connection health and status of the live data feed."""
        pass

    @abstractmethod
    async def fetch_vehicle_positions(self) -> List[VehiclePosition]:
        """Fetch current positions of active metro trains."""
        pass

    @abstractmethod
    async def fetch_service_alerts(self) -> List[ServiceAlert]:
        """Fetch active service disruptions or system alerts."""
        pass

    @abstractmethod
    async def fetch_trip_updates(self) -> List[TripUpdate]:
        """Fetch schedule adherence and delay estimates."""
        pass
