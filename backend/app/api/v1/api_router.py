from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth, crowd, schedules, predictions, alerts, analytics, datasets
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(crowd.router, prefix="/crowd", tags=["Crowd Monitoring & Heatmap"])
api_router.include_router(schedules.router, prefix="/schedules", tags=["Schedules & Frequency Optimization"])
api_router.include_router(predictions.router, prefix="/predictions", tags=["AI Demand Forecasting"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["Alerts & PA Broadcasts"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics & Reports"])
api_router.include_router(datasets.router, prefix="/datasets", tags=["Real-World Datasets & Model Retraining"])
