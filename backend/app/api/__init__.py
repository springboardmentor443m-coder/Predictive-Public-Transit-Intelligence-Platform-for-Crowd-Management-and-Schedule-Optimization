from fastapi import APIRouter

from app.api.v1 import (
    analytics,
    alerts,
    auth,
    crowd,
    predictions,
    scheduling,
    stations,
    users,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(stations.router)
api_router.include_router(crowd.router)
api_router.include_router(scheduling.router)
api_router.include_router(predictions.router)
api_router.include_router(alerts.router)
api_router.include_router(analytics.router)


@api_router.get("/health", tags=["system"])
async def health() -> dict:
    return {"status": "ok", "service": "MetroFlow API"}
