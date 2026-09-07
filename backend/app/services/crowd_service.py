import random
from datetime import datetime, timezone
from typing import List, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.models import Station
from app.schemas.crowd_schema import StationDensity, CrowdSummaryResponse
from app.ml.data_generator import STATION_METADATA, get_rush_hour_multiplier

# Live in-memory cache for fast density metrics access
live_station_state: Dict[int, dict] = {}


def initialize_live_station_states():
    now = datetime.now(timezone.utc)
    hour = now.hour
    minute = now.minute
    is_weekend = now.weekday() >= 5
    multiplier = get_rush_hour_multiplier(hour, minute, is_weekend)

    for st in STATION_METADATA:
        base_inflow = random.randint(45, 90) if not st["interchange"] else random.randint(90, 180)
        base_outflow = random.randint(40, 80) if not st["interchange"] else random.randint(80, 160)
        
        inflow = int(base_inflow * multiplier)
        outflow = int(base_outflow * multiplier * 0.9)

        # Formula: (Inflow - Outflow)/Capacity * 100 (scaled to realistic platform occupancy)
        net_occupancy = max(50, int((inflow - outflow) * 15 + st["capacity"] * 0.35 * multiplier))
        density_pct = round(min(98.5, max(5.0, (net_occupancy / st["capacity"]) * 100.0)), 1)
        
        status = "CRITICAL" if density_pct >= 80.0 else ("MODERATE" if density_pct >= 60.0 else "NORMAL")

        live_station_state[st["id"]] = {
            "station_id": st["id"],
            "station_code": st["code"],
            "station_name": st["name"],
            "line_name": st["line"],
            "inflow_rate_ppm": inflow,
            "outflow_rate_ppm": outflow,
            "current_occupancy": net_occupancy,
            "platform_capacity": st["capacity"],
            "density_percentage": density_pct,
            "status": status,
            "latitude": st["lat"],
            "longitude": st["lng"],
            "is_interchange": st["interchange"],
            "last_updated": now,
        }


# Initialize on import
initialize_live_station_states()


class CrowdService:
    @staticmethod
    async def get_all_station_densities(db: AsyncSession = None) -> List[StationDensity]:
        now = datetime.now(timezone.utc)
        results = []
        
        # Slightly fluctuate values to simulate real-time live transit updates
        for st_id, data in live_station_state.items():
            noise_in = random.randint(-3, 3)
            noise_out = random.randint(-3, 3)
            data["inflow_rate_ppm"] = max(5, data["inflow_rate_ppm"] + noise_in)
            data["outflow_rate_ppm"] = max(5, data["outflow_rate_ppm"] + noise_out)
            
            # Recalculate density
            capacity = data["platform_capacity"]
            delta = (data["inflow_rate_ppm"] - data["outflow_rate_ppm"]) * 0.2
            new_occ = max(30, int(data["current_occupancy"] + delta))
            density_pct = round(min(99.0, max(5.0, (new_occ / capacity) * 100.0)), 1)
            
            data["current_occupancy"] = new_occ
            data["density_percentage"] = density_pct
            data["status"] = "CRITICAL" if density_pct >= 80.0 else ("MODERATE" if density_pct >= 60.0 else "NORMAL")
            data["last_updated"] = now

            results.append(StationDensity(**data))

        return results

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
