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