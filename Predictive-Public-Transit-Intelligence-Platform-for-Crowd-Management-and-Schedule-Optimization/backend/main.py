from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
from backend.model import model, df

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {
        "message": "MetroFlow Backend API is running!"
    }


class PredictionRequest(BaseModel):
    hour: int
    station: str


@app.post("/predict")
def predict_ridership(request: PredictionRequest):

    # Check whether station exists
    if request.station not in df["Station"].unique():
        return {
            "error": "Station not found"
        }

    # Get station code
    station_code = df.loc[
        df["Station"] == request.station,
        "station_code"
    ].iloc[0]

    # Create prediction input
    input_data = pd.DataFrame([{
        "Hour": request.hour,
        "year": 2025,
        "month": 8,
        "day": 1,
        "day_of_week": 4,
        "station_code": station_code
    }])

    # Predict
    prediction = model.predict(input_data)[0]

    return {
        "station": request.station,
        "hour": request.hour,
        "predicted_ridership": round(float(prediction), 2)
    }