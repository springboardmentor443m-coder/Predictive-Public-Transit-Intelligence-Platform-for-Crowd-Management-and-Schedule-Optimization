import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import SessionLocal
from app.db.init_db import init_db
from app.api.v1.router import api_router
from app.services.live_data.ingestion import ingestion_service

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("metroflow.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup DB schema & seed admin check
    logger.info("Initializing MetroFlow backend lifespan...")
    try:
        db = SessionLocal()
        init_db(db)
        db.close()
    except Exception as e:
        logger.error(f"Error during startup DB initialization: {e}")

    # Initial Sync & Start Live MTA Background Ingestion Task
    try:
        logger.info("Starting live MTA GTFS-RT ingestion service background task...")
        db = SessionLocal()
        await ingestion_service.sync_once(db=db)
        db.close()
        ingestion_service.start()
    except Exception as e:
        logger.warning(f"Initial live feed sync warning: {e}")

    yield

    logger.info("Shutting down MetroFlow backend lifespan...")
    ingestion_service.stop()


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "Production-style Intelligent Metro Operations Platform API. "
        "Provides live NYC MTA Subway GTFS-Realtime ingestion, authentication, RBAC, "
        "audit logging, and real-time WebSocket event broadcasting."
    ),
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS Configuration
if settings.BACKEND_CORS_ORIGINS:
    origins = [str(origin).strip() for origin in settings.BACKEND_CORS_ORIGINS if origin]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include API Router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", include_in_schema=False)
def root():
    return {
        "title": settings.PROJECT_NAME,
        "version": "1.0.0",
        "docs": "/docs",
        "health": f"{settings.API_V1_STR}/health"
    }
