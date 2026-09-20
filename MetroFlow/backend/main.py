from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from pathlib import Path
import joblib
import pandas as pd
from pydantic import BaseModel
from app.database import Base, engine
from app.models.station import Station
from app.routes.station import router as station_router

# Load trained MetroFlow model
MODEL_PATH = (
    Path(__file__).resolve().parents[1]
    / "models"
    / "metroflow_final_ridership_model.pkl"
)

model = joblib.load(MODEL_PATH)

class PredictionInput(BaseModel):
    station: str
    hour: int
    day_of_week: int
    current_ridership: float

app = FastAPI(
    title="MetroFlow API",
    description="AI-powered Metro Crowd Management and Schedule Optimization API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def create_tables():
    Base.metadata.create_all(bind=engine)

app.include_router(station_router)

@app.post("/predict")
def predict_ridership(data: PredictionInput):

    is_weekend = int(data.day_of_week >= 5)

    is_peak_hour = int(
        data.hour in [7, 8, 9, 17, 18, 19, 20]
    )

    input_data = pd.DataFrame([{
        "Station": data.station,
        "Hour": data.hour,
        "DayOfWeek": data.day_of_week,
        "IsWeekend": is_weekend,
        "IsPeakHour": is_peak_hour,
        "Ridership": data.current_ridership
    }])

    prediction = float(model.predict(input_data)[0])

    # Ridership cannot be negative
    prediction = max(0, prediction)

    # Load station-specific crowd thresholds
    results_path = (
        Path(__file__).resolve().parents[1]
        / "datasets"
        / "processed"
        / "metroflow_predictions.csv"
    )

    results_df = pd.read_csv(results_path)

    station_data = results_df[
        results_df["Station"] == data.station
    ]

    if station_data.empty:
        crowd_level = "Unknown"
        recommendation = "Station not found in the analyzed dataset"
    else:
        medium_threshold = station_data["Medium_Threshold"].iloc[0]
        high_threshold = station_data["High_Threshold"].iloc[0]
        very_high_threshold = station_data["Very_High_Threshold"].iloc[0]

        if prediction >= very_high_threshold:
            crowd_level = "Very High"
            recommendation = "Increase service frequency and closely monitor crowding"
        elif prediction >= high_threshold:
            crowd_level = "High"
            recommendation = "Monitor station closely and consider additional service"
        elif prediction >= medium_threshold:
            crowd_level = "Medium"
            recommendation = "Maintain normal service and continue monitoring"
        else:
            crowd_level = "Low"
            recommendation = "Normal/off-peak operations"

    return {
        "station": data.station,
        "hour": data.hour,
        "current_ridership": data.current_ridership,
        "predicted_next_hour_ridership": round(prediction, 2),
        "crowd_level": crowd_level,
        "recommendation": recommendation
    }

@app.get("/")
def root():
    return {
        "message": "MetroFlow API is running",
        "status": "success",
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
    }


@app.get("/database-test")
def database_test():
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT current_database();"))
            database_name = result.fetchone()[0]

        return {
            "status": "success",
            "message": "Database connected successfully using SQLAlchemy",
            "database": database_name,
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
        }

@app.get("/analytics")
def get_analytics():
    import pandas as pd

    data_path = "../datasets/raw/station-hourly.csv"

    df = pd.read_csv(data_path, sep=";")

    total_ridership = int(df["Ridership"].sum())
    total_stations = int(df["Station"].nunique())

    busiest_station = (
        df.groupby("Station")["Ridership"]
        .sum()
        .idxmax()
    )

    peak_hour = int(
        df.groupby("Hour")["Ridership"]
        .sum()
        .idxmax()
    )

    return {
        "total_ridership": total_ridership,
        "total_stations": total_stations,
        "busiest_station": busiest_station,
        "peak_hour": peak_hour
    }