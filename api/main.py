"""
AI MetroFlow - Predictive Public Transit Intelligence Platform
FastAPI Backend Application for Real-Time Subway Crowd & Congestion Prediction
"""

import os
import sys
import time
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, ConfigDict

# Ensure src/ directory is importable
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(ROOT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from prediction import CongestionPredictor

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("MetroFlow.API")

# Global predictor instance
MODEL_PATH = os.path.join(ROOT_DIR, "models", "congestion_model.pkl")

def get_or_load_predictor() -> Optional[CongestionPredictor]:
    """Helper to lazily or eagerly load predictor singleton."""
    global predictor
    if predictor is None:
        if os.path.exists(MODEL_PATH):
            try:
                predictor = CongestionPredictor(model_path=MODEL_PATH)
                logger.info("Model loaded successfully: %s", predictor.model_name)
            except Exception as e:
                logger.error("Failed to load model from %s: %s", MODEL_PATH, e)
                predictor = None
    return predictor

# Eager initialization if model exists
predictor: Optional[CongestionPredictor] = None
get_or_load_predictor()

# Borough normalization mapping
BOROUGH_NORMALIZATION = {
    "manhattan": "M",
    "m": "M",
    "brooklyn": "Bk",
    "bk": "Bk",
    "queens": "Q",
    "q": "Q",
    "bronx": "Bx",
    "bx": "Bx",
    "staten island": "SI",
    "si": "SI",
}

# Concise operational transit recommendations
CONCISE_RECOMMENDATIONS = {
    "High": "Increase train frequency.",
    "Medium": "Maintain standard schedule. Monitor passenger density.",
    "Low": "Standard or reduced frequency is sufficient.",
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for loading ML artifacts on startup and cleaning up."""
    get_or_load_predictor()
    yield
    logger.info("Shutting down MetroFlow API service...")


# Initialize FastAPI App
app = FastAPI(
    title="AI MetroFlow: Public Transit Intelligence Platform",
    description=(
        "Predictive intelligence platform for subway crowd management and schedule optimization. "
        "Predicts congestion levels (Low, Medium, High) using real-time and scheduled transit features."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Enable CORS for frontend / dashboard integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request Logging Middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration_ms = round((time.time() - start_time) * 1000, 2)
    logger.info(
        "%s %s - Status: %d - Duration: %sms",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


# =====================================================================
# Pydantic Schemas
# =====================================================================

class PredictionRequest(BaseModel):
    """Pydantic schema for single subway congestion prediction request."""
    hour: int = Field(..., ge=0, le=23, description="Hour of the day (0-23)", example=8)
    day: int = Field(..., ge=1, le=31, description="Day of the month (1-31)", example=15)
    month: int = Field(..., ge=1, le=12, description="Month of the year (1-12)", example=9)
    year: int = Field(..., ge=2015, le=2030, description="Year", example=2021)
    day_of_week: int = Field(..., ge=0, le=6, description="Day of week (0=Mon, 6=Sun)", example=2)
    is_weekend: Optional[int] = Field(None, ge=0, le=1, description="Weekend flag (1=weekend, 0=weekday)", example=0)
    is_peak_hour: Optional[int] = Field(None, ge=0, le=1, description="Peak rush hour flag (1=peak, 0=off-peak)", example=1)
    Latitude: float = Field(..., ge=-90.0, le=90.0, description="Station Latitude coordinate", example=40.7527)
    Longitude: float = Field(..., ge=-180.0, le=180.0, description="Station Longitude coordinate", example=-73.9772)
    Borough: str = Field(..., description="Borough name or code (e.g. 'Manhattan' or 'M')", example="Manhattan")
    Structure: str = Field(..., description="Station physical structure (e.g. 'Subway', 'Elevated')", example="Subway")
    stop_name: str = Field(..., alias="Stop Name", description="Subway stop/station name", example="Grand Central - 42 St")

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "hour": 8,
                "day": 15,
                "month": 9,
                "year": 2021,
                "day_of_week": 2,
                "is_weekend": 0,
                "is_peak_hour": 1,
                "Latitude": 40.7527,
                "Longitude": -73.9772,
                "Borough": "Manhattan",
                "Structure": "Subway",
                "Stop Name": "Grand Central - 42 St"
            }
        }
    )


class PredictionResponse(BaseModel):
    """Pydantic schema for prediction output."""
    congestion_level: str = Field(..., description="Predicted congestion level ('Low', 'Medium', 'High')", example="High")
    confidence: float = Field(..., description="Confidence probability score for predicted class", example=0.98)
    recommendation: str = Field(..., description="Actionable transit dispatch recommendation", example="Increase train frequency.")
    probabilities: Optional[Dict[str, float]] = Field(None, description="Probability distribution across all tiers")


class HealthResponse(BaseModel):
    """Pydantic schema for API health status."""
    status: str
    model_loaded: bool
    model_name: Optional[str]
    model_path: str
    timestamp: str


# =====================================================================
# API Endpoints
# =====================================================================

@app.get("/", tags=["General"])
def read_root():
    """Welcome endpoint providing service metadata and documentation links."""
    return {
        "service": "AI MetroFlow Predictive Transit Intelligence Platform",
        "status": "online",
        "documentation": "/docs",
        "redoc": "/redoc",
        "endpoints": {
            "health": "/health",
            "predict": "/predict (POST)",
            "batch_predict": "/predict/batch (POST)"
        },
        "model_loaded": predictor is not None,
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
def health_check():
    """Health check endpoint to verify API operation and ML model readiness."""
    is_ready = predictor is not None
    return HealthResponse(
        status="healthy" if is_ready else "degraded",
        model_loaded=is_ready,
        model_name=predictor.model_name if is_ready else None,
        model_path=MODEL_PATH,
        timestamp=datetime.utcnow().isoformat(),
    )


@app.post(
    "/predict",
    response_model=PredictionResponse,
    status_code=status.HTTP_200_OK,
    tags=["Prediction"],
    summary="Predict Subway Congestion Level",
    description="Accepts transit station and temporal parameters and predicts congestion level with confidence score.",
)
def predict_congestion(payload: PredictionRequest):
    """
    Executes real-time subway congestion prediction.
    """
    global predictor
    if predictor is None:
        try:
            logger.info("Attempting lazy model loading...")
            predictor = CongestionPredictor(model_path=MODEL_PATH)
        except Exception as e:
            logger.error("Model unavailable: %s", e)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Machine learning model artifact is not loaded: {str(e)}",
            )

    try:
        # Extract payload and normalize Borough name to single-letter code if needed
        data = payload.model_dump(by_alias=True)
        raw_borough = str(data.get("Borough", "")).strip().lower()
        normalized_borough = BOROUGH_NORMALIZATION.get(raw_borough, data.get("Borough"))
        data["Borough"] = normalized_borough

        # Run inference using CongestionPredictor
        result = predictor.predict(data)

        # Get concise recommendation matching project spec
        pred_level = result["congestion_level"]
        concise_rec = CONCISE_RECOMMENDATIONS.get(
            pred_level,
            result.get("recommendation", "Monitor station real-time telemetry.")
        )

        return PredictionResponse(
            congestion_level=pred_level,
            confidence=round(result["confidence"], 2),
            recommendation=concise_rec,
            probabilities=result.get("probabilities"),
        )
    except Exception as e:
        logger.exception("Inference error occurred: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inference processing failed: {str(e)}",
        )


@app.post(
    "/predict/batch",
    response_model=List[PredictionResponse],
    status_code=status.HTTP_200_OK,
    tags=["Prediction"],
    summary="Batch Subway Congestion Prediction",
    description="Accepts a list of transit stations and returns predictions for each.",
)
def predict_batch(payload: List[PredictionRequest]):
    """Executes high-throughput batch prediction."""
    global predictor
    if predictor is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Machine learning model is not loaded.",
        )

    results = []
    for item in payload:
        data = item.model_dump(by_alias=True)
        raw_borough = str(data.get("Borough", "")).strip().lower()
        data["Borough"] = BOROUGH_NORMALIZATION.get(raw_borough, data.get("Borough"))
        
        res = predictor.predict(data)
        pred_level = res["congestion_level"]
        results.append(
            PredictionResponse(
                congestion_level=pred_level,
                confidence=round(res["confidence"], 2),
                recommendation=CONCISE_RECOMMENDATIONS.get(pred_level, res.get("recommendation")),
                probabilities=res.get("probabilities"),
            )
        )
    return results


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
