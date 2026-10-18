import os
import joblib
import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from app.datasets.pipeline import pipeline_engine, PROCESSED_DIR
from app.ml.train_bmrcl_models import train_bmrcl_ml_pipeline, SAVED_MODELS_DIR

router = APIRouter()


class DatasetStatsResponse(BaseModel):
    total_records: int
    data_sources: List[str]
    date_range: str
    master_file_exists: bool
    last_trained_r2: Optional[float] = None
    last_trained_mae: Optional[float] = None


@router.get("/stats", response_model=DatasetStatsResponse)
async def get_dataset_stats():
    parquet_path = os.path.join(PROCESSED_DIR, "master_bmrcl_ridership.parquet")
    csv_path = os.path.join(PROCESSED_DIR, "master_transit_dataset.csv")
    total_records = 0
    date_range = "N/A"
    exists = os.path.exists(parquet_path) or os.path.exists(csv_path)

    if os.path.exists(parquet_path):
        try:
            df = pd.read_parquet(parquet_path)
            total_records = len(df)
            date_range = f"{df['timestamp'].min()} to {df['timestamp'].max()}"
        except Exception:
            pass
    elif os.path.exists(csv_path):
        try:
            df = pd.read_csv(csv_path)
            total_records = len(df)
            date_range = f"{df['timestamp'].min()} to {df['timestamp'].max()}"
        except Exception:
            pass

    # Read saved model metrics from BMRCL training artifact
    r2, mae = None, None
    demand_path = os.path.join(SAVED_MODELS_DIR, "demand_forecaster.joblib")
    if os.path.exists(demand_path):
        try:
            data = joblib.load(demand_path)
            metrics = data.get("metrics", {})
            r2 = metrics.get("r2_1h", metrics.get("r2_15"))
            mae = metrics.get("mae_1h", metrics.get("mae_15"))
        except Exception:
            pass

    return DatasetStatsResponse(
        total_records=total_records,
        data_sources=[
            "BMRCL GTFS (OpenStreetMap & Timetable)",
            "BMRCL RTI Ridership (August 2025)",
            "BMRCL RTI Ridership (September 2025)"
        ],
        date_range=date_range,
        master_file_exists=exists,
        last_trained_r2=r2,
        last_trained_mae=mae,
    )


@router.post("/ingest")
async def trigger_dataset_ingestion():
    try:
        stats = pipeline_engine.run_pipeline()
        return {"status": "SUCCESS", "message": "BMRCL datasets ingested & normalized.", "details": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@router.post("/retrain")
async def trigger_model_retraining():
    try:
        pipeline_engine.run_pipeline()
        demand_metrics = train_bmrcl_ml_pipeline()

        return {
            "status": "SUCCESS",
            "message": "AI Demand Forecaster & Anomaly Detector retrained on real BMRCL data.",
            "metrics": demand_metrics.get("metrics", {}),
            "dataset_rows": demand_metrics.get("dataset_rows", 0),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Retraining failed: {str(e)}")
