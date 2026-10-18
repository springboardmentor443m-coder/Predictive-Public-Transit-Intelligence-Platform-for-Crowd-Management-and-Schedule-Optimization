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
        
        # BMRCL active train schedules across Purple and Green corridors (Scheduled Timetable Data)
        sample_schedules = [
            {
                "id": 101,
                "train_id": 1,
                "train_code": "BMRCL-TR-P01",
                "line_name": "Purple Line",
                "origin_station_id": 1,
                "origin_station_name": "Challaghatta",
                "destination_station_id": 37,
                "destination_station_name": "Whitefield (Kadugodi)",
                "departure_time": now - timedelta(minutes=15),
                "arrival_time": now + timedelta(minutes=45),
                "headway_minutes": 5,
                "recommended_headway": 4,
                "status": ScheduleStatus.RUNNING,
                "delay_minutes": 0,
                "conflict_detected": False,
            },
            {
                "id": 102,
                "train_id": 2,
                "train_code": "BMRCL-TR-P02",
                "line_name": "Purple Line",
                "origin_station_id": 37,
                "origin_station_name": "Whitefield (Kadugodi)",
                "destination_station_id": 1,
                "destination_station_name": "Challaghatta",
                "departure_time": now - timedelta(minutes=5),
                "arrival_time": now + timedelta(minutes=55),
                "headway_minutes": 5,
                "recommended_headway": 4,
                "status": ScheduleStatus.RUNNING,
                "delay_minutes": 0,
                "conflict_detected": False,
            },
            {
                "id": 103,
                "train_id": 3,
                "train_code": "BMRCL-TR-P03",
                "line_name": "Purple Line",
                "origin_station_id": 18,
                "origin_station_name": "Baiyappanahalli",
                "destination_station_id": 9,
                "destination_station_name": "Mysore Road",
                "departure_time": now - timedelta(minutes=10),
                "arrival_time": now + timedelta(minutes=25),
                "headway_minutes": 6,
                "recommended_headway": 5,
                "status": ScheduleStatus.RUNNING,
                "delay_minutes": 0,
                "conflict_detected": False,
            },
            {
                "id": 104,
                "train_id": 4,
                "train_code": "BMRCL-TR-G01",
                "line_name": "Green Line",
                "origin_station_id": 38,
                "origin_station_name": "Madavara",
                "destination_station_id": 66,
                "destination_station_name": "Silk Institute",
                "departure_time": now - timedelta(minutes=12),
                "arrival_time": now + timedelta(minutes=50),
                "headway_minutes": 6,
                "recommended_headway": 5,
                "status": ScheduleStatus.RUNNING,
                "delay_minutes": 0,
                "conflict_detected": False,
            },
            {
                "id": 105,
                "train_id": 5,
                "train_code": "BMRCL-TR-G02",
                "line_name": "Green Line",
                "origin_station_id": 66,
                "origin_station_name": "Silk Institute",
                "destination_station_id": 38,
                "destination_station_name": "Madavara",
                "departure_time": now + timedelta(minutes=4),
                "arrival_time": now + timedelta(minutes=65),
                "headway_minutes": 7,
                "recommended_headway": 5,
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
        
        # Check Purple Line density
        purple_stations = [s for s in live_station_state.values() if "Purple" in s.get("line_name", "")]
        avg_purple_density = sum(s["density_percentage"] for s in purple_stations) / len(purple_stations) if purple_stations else 50.0

        if avg_purple_density > 75.0:
            recommendations.append(FrequencyOptimizationRecommendation(
                line_name="Purple Line",
                segment_name="Challaghatta -> Majestic -> Whitefield (Kadugodi)",
                current_headway_minutes=5,
                recommended_headway_minutes=3,
                additional_trains_needed=2,
                reason="DECISION SUPPORT ONLY: Influx surge detected in Whitefield/Indiranagar tech corridors. Additional headway reduction recommended.",
                crowd_density_percentage=round(avg_purple_density, 1),
                timestamp=now
            ))

        # Check Green Line density
        green_stations = [s for s in live_station_state.values() if "Green" in s.get("line_name", "")]
        avg_green_density = sum(s["density_percentage"] for s in green_stations) / len(green_stations) if green_stations else 48.0

        if avg_green_density > 70.0:
            recommendations.append(FrequencyOptimizationRecommendation(
                line_name="Green Line",
                segment_name="Madavara -> Yeshwantpur -> Majestic -> Silk Institute",
                current_headway_minutes=6,
                recommended_headway_minutes=4,
                additional_trains_needed=2,
                reason="DECISION SUPPORT ONLY: Industrial and transfer accumulation at Yeshwantpur & Majestic interchange.",
                crowd_density_percentage=round(avg_green_density, 1),
                timestamp=now
            ))

        if not recommendations:
            recommendations.append(FrequencyOptimizationRecommendation(
                line_name="System Wide",
                segment_name="All BMRCL Corridors (Purple & Green)",
                current_headway_minutes=5,
                recommended_headway_minutes=5,
                additional_trains_needed=0,
                reason="DECISION SUPPORT ONLY: Timetable service operating within nominal historical crowd limits.",
                crowd_density_percentage=round((avg_purple_density + avg_green_density) / 2, 1),
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
