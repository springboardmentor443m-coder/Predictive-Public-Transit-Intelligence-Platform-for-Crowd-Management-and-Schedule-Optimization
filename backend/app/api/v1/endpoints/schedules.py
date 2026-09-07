from typing import List
from fastapi import APIRouter
from app.services.schedule_service import schedule_service
from app.schemas.schedule_schema import (
    ScheduleResponse, FrequencyOptimizationRecommendation, ScheduleOverrideRequest
)

router = APIRouter()


@router.get("/", response_model=List[ScheduleResponse])
async def get_active_schedules():
    return await schedule_service.get_active_schedules()


@router.get("/optimizations", response_model=List[FrequencyOptimizationRecommendation])
async def get_frequency_optimizations():
    return await schedule_service.get_frequency_recommendations()


@router.post("/override")
async def override_schedule(request: ScheduleOverrideRequest):
    return await schedule_service.override_schedule(request)
