from typing import List
from fastapi import APIRouter
from app.services.crowd_service import crowd_service
from app.schemas.crowd_schema import StationDensity, CrowdSummaryResponse, HeatmapPoint

router = APIRouter()


@router.get("/densities", response_model=List[StationDensity])
async def get_station_densities():
    return await crowd_service.get_all_station_densities()


@router.get("/summary", response_model=CrowdSummaryResponse)
async def get_crowd_summary():
    return await crowd_service.get_crowd_summary()


@router.get("/heatmap", response_model=List[HeatmapPoint])
async def get_heatmap_data():
    densities = await crowd_service.get_all_station_densities()
    return [
        HeatmapPoint(
            station_id=d.station_id,
            name=d.station_name,
            latitude=d.latitude,
            longitude=d.longitude,
            density_percentage=d.density_percentage,
            status=d.status,
            line_name=d.line_name
        )
        for d in densities
    ]
