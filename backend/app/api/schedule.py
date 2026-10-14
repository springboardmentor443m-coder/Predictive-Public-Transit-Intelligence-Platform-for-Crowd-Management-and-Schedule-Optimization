from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

router = APIRouter(prefix="/api/schedule", tags=["Schedule Optimization"])

class DispatchAction(BaseModel):
    corridor_id: str
    action_type: str
    target_headway_min: float

@router.get("/forecasts")
def get_predictive_forecasts():
    return {
        "prediction_horizon_min": 60,
        "corridors": [
            {
                "id": "blue-corridor",
                "name": "Blue Corridor",
                "current_headway_min": 5.0,
                "recommended_headway_min": 3.0,
                "predicted_peak_inflow": 420,
                "surge_risk_score": 87,
                "status": "ACTION_REQUIRED",
                "trend": [
                    {"time": "+15m", "predicted_passengers": 280},
                    {"time": "+30m", "predicted_passengers": 360},
                    {"time": "+45m", "predicted_passengers": 420},
                    {"time": "+60m", "predicted_passengers": 390}
                ]
            },
            {
                "id": "emerald-express",
                "name": "Emerald Express",
                "current_headway_min": 6.5,
                "recommended_headway_min": 6.5,
                "predicted_peak_inflow": 160,
                "surge_risk_score": 32,
                "status": "OPTIMAL",
                "trend": [
                    {"time": "+15m", "predicted_passengers": 130},
                    {"time": "+30m", "predicted_passengers": 150},
                    {"time": "+45m", "predicted_passengers": 160},
                    {"time": "+60m", "predicted_passengers": 140}
                ]
            },
            {
                "id": "ruby-loop",
                "name": "Ruby Loop",
                "current_headway_min": 8.0,
                "recommended_headway_min": 5.0,
                "predicted_peak_inflow": 310,
                "surge_risk_score": 74,
                "status": "ACTION_REQUIRED",
                "trend": [
                    {"time": "+15m", "predicted_passengers": 190},
                    {"time": "+30m", "predicted_passengers": 250},
                    {"time": "+45m", "predicted_passengers": 310},
                    {"time": "+60m", "predicted_passengers": 290}
                ]
            }
        ]
    }

@router.post("/dispatch")
def trigger_dispatch(action: DispatchAction):
    return {
        "status": "SUCCESS",
        "corridor_id": action.corridor_id,
        "applied_headway_min": action.target_headway_min,
        "message": f"Schedule optimized for {action.corridor_id}. Fleet auto-dispatch sequence acknowledged."
    }