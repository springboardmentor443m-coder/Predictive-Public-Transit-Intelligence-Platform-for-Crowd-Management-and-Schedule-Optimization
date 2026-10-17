from fastapi import APIRouter
from app.api.v1 import health, auth, profile, users, audit, websocket, live, ml, alerts

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(auth.router, tags=["Authentication"])
api_router.include_router(profile.router, tags=["User Profile"])
api_router.include_router(users.router, tags=["Admin User Management"])
api_router.include_router(audit.router, tags=["Audit Logs"])
api_router.include_router(websocket.router, tags=["Real-time Infrastructure"])
api_router.include_router(live.router, tags=["Live MTA Transit Ingestion"])
api_router.include_router(ml.router, tags=["ML Demand & Risk Intelligence"])
api_router.include_router(alerts.router, tags=["Alert & Notification Intelligence"])

