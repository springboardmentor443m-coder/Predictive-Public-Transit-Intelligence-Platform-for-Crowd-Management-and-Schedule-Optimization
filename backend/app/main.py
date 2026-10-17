from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.models import user
from app.models import scheduling
from app.routers import health, auth, crowd, scheduling, prediction
from app.routers.monitoring import router as monitoring_router
from app.routers.alerts import router as alerts_router
from app.routers.operations import router as operations_router
from app.routers.analytics import router as analytics_router

Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="AI MetroFlow API",
    description="Backend API for the AI-powered metro crowd management and scheduling platform.",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(health.router)
app.include_router(auth.router)
app.include_router(crowd.router)
app.include_router(scheduling.router)
app.include_router(prediction.router)
app.include_router(monitoring_router)
app.include_router(alerts_router)
app.include_router(operations_router)
app.include_router(analytics_router)


@app.get("/")
def root():
    return {
        "message": "Welcome to AI MetroFlow",
        "status": "Backend is running"
    }
