from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from backend.model import model, df

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PredictionRequest(BaseModel):
    station: str
    hour: int


def get_crowd_level(predicted_ridership):

    if predicted_ridership < 100:
        return "LOW"

    elif predicted_ridership < 300:
        return "MEDIUM"

    else:
        return "HIGH"


@app.get("/")
def home():
    return {"message": "MetroFlow Backend API is running!"}


@app.post("/predict")
def predict(data: PredictionRequest):

    station = data.station
    hour = data.hour

    # Check whether station exists
    if station not in df["Station"].unique():
        return {"error": "Station not found"}

    # Get station code
    station_code = df.loc[
        df["Station"] == station,
        "station_code"
    ].iloc[0]

    # Use the latest date available in the dataset
    latest_date = df["Date"].max()

    year = latest_date.year
    month = latest_date.month
    day = latest_date.day
    day_of_week = latest_date.dayofweek

    # Create input for Random Forest model
    input_data = [[
        hour,
        year,
        month,
        day,
        day_of_week,
        station_code
    ]]

    # Make prediction using Random Forest
    predicted_ridership = model.predict(input_data)[0]

    # Determine crowd level
    crowd_level = get_crowd_level(predicted_ridership)

    # Return prediction and crowd information
    return {
        "station": station,
        "hour": hour,
        "predicted_ridership": round(float(predicted_ridership), 2),
        "crowd_level": crowd_level
    }