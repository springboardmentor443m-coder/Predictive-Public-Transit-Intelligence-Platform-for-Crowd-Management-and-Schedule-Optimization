from datetime import datetime, timedelta, timezone
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.models.models import Schedule, Train, Station, ScheduleStatus
from app.schemas.schedule_schema import (
    ScheduleResponse, FrequencyOptimizationRecommendation, ScheduleOverrideRequest
)
from app.services.crowd_service import live_station_state


class ScheduleService:
    @staticmethod
    async def get_active_schedules(db: AsyncSession = None) -> List[ScheduleResponse]:
        now = datetime.now(timezone.utc)
        
        # Mock active train schedules based on Red Line and Blue Line runs
        sample_schedules = [
            {
                "id": 101,
                "train_id": 1,
                "train_code": "RED-TR-01",
                "line_name": "Red Line",
                "origin_station_id": 1,
                "origin_station_name": "Central Terminal",
                "destination_station_id": 8,
                "destination_station_name": "Suburban North",
                "departure_time": now - timedelta(minutes=15),
                "arrival_time": now + timedelta(minutes=25),
                "headway_minutes": 5,
                "recommended_headway": 4,
                "status": ScheduleStatus.RUNNING,
                "delay_minutes": 0,
                "conflict_detected": False,
            },
            {
                "id": 102,
                "train_id": 2,
                "train_code": "RED-TR-02",
                "line_name": "Red Line",
                "origin_station_id": 8,
                "origin_station_name": "Suburban North",
                "destination_station_id": 1,
                "destination_station_name": "Central Terminal",
                "departure_time": now - timedelta(minutes=5),
                "arrival_time": now + timedelta(minutes=35),
                "headway_minutes": 6,
                "recommended_headway": 4,
                "status": ScheduleStatus.RUNNING,
                "delay_minutes": 4,
                "conflict_detected": False,
            },
            {
                "id": 103,
                "train_id": 3,
                "train_code": "BLU-TR-01",
                "line_name": "Blue Line",
                "origin_station_id": 9,
                "origin_station_name": "West Port",
                "destination_station_id": 16,
                "destination_station_name": "East terminus",
                "departure_time": now - timedelta(minutes=20),
                "arrival_time": now + timedelta(minutes=20),
                "headway_minutes": 7,
                "recommended_headway": 5,
                "status": ScheduleStatus.DELAYED,
                "delay_minutes": 8,
                "conflict_detected": True,
                "conflict_reason": "Platform occupancy conflict at Central Terminal interchange node.",
            },
            {
                "id": 104,
                "train_id": 4,
                "train_code": "BLU-TR-02",
                "line_name": "Blue Line",
                "origin_station_id": 16,
                "origin_station_name": "East terminus",
                "destination_station_id": 9,
                "destination_station_name": "West Port",
                "departure_time": now + timedelta(minutes=10),
                "arrival_time": now + timedelta(minutes=50),
                "headway_minutes": 6,
                "recommended_headway": 6,
                "status": ScheduleStatus.SCHEDULED,
                "delay_minutes": 0,
                "conflict_detected": False,
            },
        ]
        return [ScheduleResponse(**s) for s in sample_schedules]

    @staticmethod
    async def get_frequency_recommendations() -> List[FrequencyOptimizationRecommendation]:
        recommendations = []
        now = datetime.now(timezone.utc)
        
        # Check Red Line density
        red_stations = [s for s in live_station_state.values() if s["line_name"] == "Red Line"]
        avg_red_density = sum(s["density_percentage"] for s in red_stations) / len(red_stations) if red_stations else 50.0

        if avg_red_density > 75.0:
            recommendations.append(FrequencyOptimizationRecommendation(
                line_name="Red Line",
                segment_name="Central Terminal -> Tech Hub North",
                current_headway_minutes=6,
                recommended_headway_minutes=4,
                additional_trains_needed=2,
                reason="Passenger crowd density exceeds 75% peak threshold. Deploying +2 trains/hr mitigates bottleneck.",
                crowd_density_percentage=round(avg_red_density, 1),
                timestamp=now
            ))

        # Check Blue Line density
        blue_stations = [s for s in live_station_state.values() if s["line_name"] == "Blue Line"]
        avg_blue_density = sum(s["density_percentage"] for s in blue_stations) / len(blue_stations) if blue_stations else 50.0

        if avg_blue_density > 70.0:
            recommendations.append(FrequencyOptimizationRecommendation(
                line_name="Blue Line",
                segment_name="Civic Center -> Stadium Arena",
                current_headway_minutes=8,
                recommended_headway_minutes=5,
                additional_trains_needed=2,
                reason="High footfall surge detected at Stadium Arena interchange node. Frequency increase recommended.",
                crowd_density_percentage=round(avg_blue_density, 1),
                timestamp=now
            ))

        if not recommendations:
            recommendations.append(FrequencyOptimizationRecommendation(
                line_name="System Wide",
                segment_name="All Transit Corridors",
                current_headway_minutes=6,
                recommended_headway_minutes=6,
                additional_trains_needed=0,
                reason="Current headway optimal. Network operating within nominal crowd limits.",
                crowd_density_percentage=round((avg_red_density + avg_blue_density)/2, 1),
                timestamp=now
            ))

        return recommendations

    @staticmethod
    async def override_schedule(request: ScheduleOverrideRequest) -> dict:
        # Check for headway conflicts (< 2 minutes minimum safety headway)
        conflict_detected = False
        conflict_msg = None

        if request.new_headway_minutes < 3:
            conflict_detected = True
            conflict_msg = f"Safety Violation: Headway of {request.new_headway_minutes} min is below minimum safe headway threshold (3 mins)."

        return {
            "schedule_id": request.schedule_id,
            "applied": not conflict_detected,
            "new_headway_minutes": request.new_headway_minutes,
            "conflict_detected": conflict_detected,
            "message": conflict_msg or f"Successfully updated schedule headway to {request.new_headway_minutes} mins.",
            "timestamp": datetime.now(timezone.utc)
        }


schedule_service = ScheduleService()
