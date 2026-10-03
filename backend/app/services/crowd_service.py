from datetime import datetime, timezone
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.crowd_schema import StationDensity, CrowdSummaryResponse
from app.services.realtime_passenger_service import realtime_passenger_service
from app.ml.data_generator import STATION_METADATA

# Global state dictionary for real BMRCL station density data
live_station_state: Dict[int, Dict[str, Any]] = {}

def _init_live_station_state():
    now = datetime.now(timezone.utc)
    for st in STATION_METADATA:
        live_station_state[st["id"]] = {
            "station_id": st["id"],
            "station_code": st["code"],
            "station_name": st["name"],
            "line_name": st["line"],
            "density_percentage": 42.0,
            "inflow_rate_ppm": 250,
            "outflow_rate_ppm": 220,
            "current_occupancy": 250,
            "platform_capacity": st["capacity"],
            "status": "NORMAL",
            "latitude": st["lat"],
            "longitude": st["lng"],
            "is_interchange": st["interchange"],
            "last_updated": now,
        }

_init_live_station_state()


class CrowdService:
    """
    BMRCL Crowd Telemetry Service.
    Derives real crowd densities directly from genuine historical RTI observations.
    Categorization: MetroFlow Derived Demand Classification (NORMAL <50%, MODERATE 50-80%, CRITICAL >=80%).
    """

    @staticmethod
    async def get_all_station_densities(db: AsyncSession = None) -> List[StationDensity]:
        cached = realtime_passenger_service.get_cached_station_densities()
        if not cached:
            # Fetch telemetry frame from real historical replay
            await realtime_passenger_service.get_live_telemetry()
            cached = realtime_passenger_service.get_cached_station_densities()

        # Update live_station_state dict with latest observations
        for d in cached:
            live_station_state[d.station_id] = {
                "station_id": d.station_id,
                "station_code": d.station_code,
                "station_name": d.station_name,
                "line_name": d.line_name,
                "density_percentage": d.density_percentage,
                "inflow_rate_ppm": d.inflow_rate_ppm,
                "outflow_rate_ppm": d.outflow_rate_ppm,
                "current_occupancy": d.current_occupancy,
                "platform_capacity": d.platform_capacity,
                "status": d.status,
                "latitude": d.latitude,
                "longitude": d.longitude,
                "is_interchange": d.is_interchange,
                "last_updated": d.last_updated,
            }

        return cached

    @staticmethod
    async def get_crowd_summary() -> CrowdSummaryResponse:
        densities = await CrowdService.get_all_station_densities()
        total_occ = sum(d.current_occupancy for d in densities)
        avg_density = round(sum(d.density_percentage for d in densities) / len(densities), 1) if densities else 0.0
        
        critical_count = sum(1 for d in densities if d.status == "CRITICAL")
        moderate_count = sum(1 for d in densities if d.status == "MODERATE")
        normal_count = sum(1 for d in densities if d.status == "NORMAL")

        return CrowdSummaryResponse(
            total_system_occupancy=total_occ,
            average_density_percentage=avg_density,
            critical_stations_count=critical_count,
            moderate_stations_count=moderate_count,
            normal_stations_count=normal_count,
            stations=densities
        )


crowd_service = CrowdService()

