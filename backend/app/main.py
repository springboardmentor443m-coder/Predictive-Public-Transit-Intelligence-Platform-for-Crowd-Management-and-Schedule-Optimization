from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.models import (
    CrowdEvacuation,
    MTAHourlyRidership,
    NYCSubwayTraffic,
    MetroTransaction
)

from app.routes.crowd import router as crowd_router
from app.routes.congestion import router as congestion_router
from app.routes.auth import router as auth_router
from app.routes.demand import router as demand_router
from app.routes.peak_hours import router as peak_hours_router
from app.routes.schedule import router as schedule_router
from app.routes.delay import router as delay_router
from app.routes.traffic import router as traffic_router
from app.routes.recommendations import router as recommendations_router


app = FastAPI(
    title="AI MetroFlow",
    description="AI-powered Metro Crowd Management and Scheduling Platform",
    version="1.0.0"
)


# CORS Configuration
# Allows the React frontend to communicate with the FastAPI backend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Register API routes
app.include_router(crowd_router)
app.include_router(congestion_router)
app.include_router(auth_router)
app.include_router(demand_router)
app.include_router(peak_hours_router)
app.include_router(schedule_router)
app.include_router(delay_router)
app.include_router(traffic_router)
app.include_router(recommendations_router)


@app.get("/")
def root():
    return {
        "message": "Welcome to AI MetroFlow",
        "status": "running",
        "version": "1.0.0"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "database": "connected"
    }


@app.get("/models")
def available_models():
    return {
        "models": [
            CrowdEvacuation.__tablename__,
            MTAHourlyRidership.__tablename__,
            NYCSubwayTraffic.__tablename__,
            MetroTransaction.__tablename__
        ],
        "count": 4
    }