from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.database import engine, Base
from app.ml.model_loader import ml_model
from app.routers import stations, predict, schedule, alerts, auth, analytics


from app.services.scheduler import start_scheduler, shutdown_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure database is reachable with retry loop
    print("[MetroFlow API] Initializing server and verifying database connection...")
    import time
    from sqlalchemy import text
    
    max_retries = 10
    retry_interval = 2
    for attempt in range(1, max_retries + 1):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print(f"[MetroFlow API] Database connection established successfully (attempt {attempt}).")
            break
        except Exception as e:
            if attempt < max_retries:
                print(f"[MetroFlow API] Waiting for database to become ready... (attempt {attempt}/{max_retries}): {e}")
                time.sleep(retry_interval)
            else:
                print(f"[MetroFlow API] Warning: Database connection failed after {max_retries} attempts: {e}")

    # Preload ML model and start APScheduler background monitoring
    _ = ml_model.is_loaded
    start_scheduler(interval_minutes=5)
    yield
    # Shutdown: Clean up background jobs
    print("[MetroFlow API] Shutting down server...")
    shutdown_scheduler()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description=(
        "MetroFlow AI Platform API: Real-time crowd density prediction, "
        "smart train scheduling recommendations, and automated incident alerting "
        "for the Seoul Subway Network."
    ),
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan,
)

# Configure Cross-Origin Resource Sharing (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers under /api/v1 and root prefixes for compatibility
app.include_router(stations.router, prefix=settings.API_V1_STR)
app.include_router(predict.router, prefix=settings.API_V1_STR)
app.include_router(schedule.router, prefix=settings.API_V1_STR)
app.include_router(alerts.router, prefix=settings.API_V1_STR)
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(analytics.router, prefix=settings.API_V1_STR)

# Also expose direct root paths for direct endpoint convenience
app.include_router(stations.router)
app.include_router(predict.router)
app.include_router(schedule.router)
app.include_router(alerts.router)
app.include_router(auth.router)
app.include_router(analytics.router)


@app.get("/health", tags=["Health"])
def health_check():
    """System health check endpoint."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "model_loaded": ml_model.is_loaded,
    }


@app.get("/", tags=["Health"])
def root_info():
    """Root metadata and API documentation redirect."""
    return {
        "message": "Welcome to MetroFlow AI API",
        "docs_url": f"{settings.API_V1_STR}/docs",
        "health_check": "/health",
    }
