from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from backend.model import model, df

app = FastAPI()


# =====================================================
# CORS
# =====================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =====================================================
# Prediction Request
# =====================================================

class PredictionRequest(BaseModel):
    station: str
    hour: int


# =====================================================
# Crowd Level Function
# =====================================================

def get_crowd_level(predicted_ridership):

    if predicted_ridership < 100:
        return "LOW"

    elif predicted_ridership < 300:
        return "MEDIUM"

    else:
        return "HIGH"


# =====================================================
# Crowd Alert Function
# =====================================================

def get_crowd_alert(crowd_level):

    if crowd_level == "HIGH":

        return {
            "alert": "Heavy crowd expected",
            "recommended_action":
                "Increase train frequency and monitor station congestion"
        }

    elif crowd_level == "MEDIUM":

        return {
            "alert": "Moderate crowd expected",
            "recommended_action":
                "Monitor passenger flow and station activity"
        }

    else:

        return {
            "alert": "Low crowd expected",
            "recommended_action":
                "Maintain normal train operations"
        }


# =====================================================
# Home API
# =====================================================

@app.get("/")
def home():

    return {
        "message": "MetroFlow Backend API is running!"
    }


# =====================================================
# Prediction API
# =====================================================

@app.post("/predict")
def predict(data: PredictionRequest):

    station = data.station
    hour = data.hour

    # ---------------------------------------------
    # Check whether station exists
    # ---------------------------------------------

    if station not in df["Station"].unique():

        return {
            "error": "Station not found"
        }

    # ---------------------------------------------
    # Get station code
    # ---------------------------------------------

    station_code = df.loc[
        df["Station"] == station,
        "station_code"
    ].iloc[0]

    # ---------------------------------------------
    # Get latest date
    # ---------------------------------------------

    latest_date = df["Date"].max()

    year = latest_date.year
    month = latest_date.month
    day = latest_date.day
    day_of_week = latest_date.dayofweek

    # ---------------------------------------------
    # Create model input
    # ---------------------------------------------

    input_data = [[
        hour,
        year,
        month,
        day,
        day_of_week,
        station_code
    ]]

    # ---------------------------------------------
    # Prediction
    # ---------------------------------------------

    predicted_ridership = model.predict(input_data)[0]

    predicted_ridership = round(
        float(predicted_ridership),
        2
    )

    # ---------------------------------------------
    # Crowd level
    # ---------------------------------------------

    crowd_level = get_crowd_level(
        predicted_ridership
    )

    # ---------------------------------------------
    # Crowd alert
    # ---------------------------------------------

    crowd_alert = get_crowd_alert(
        crowd_level
    )

    # ---------------------------------------------
    # Return prediction
    # ---------------------------------------------

    return {
        "station": station,
        "hour": hour,
        "predicted_ridership": predicted_ridership,
        "crowd_level": crowd_level,
        "alert": crowd_alert["alert"],
        "recommended_action":
            crowd_alert["recommended_action"]
    }


# =====================================================
# ANALYTICS API
# =====================================================

@app.get("/analytics")
def analytics():

    # Make a copy so analytics
    # does not modify the original dataset

    analytics_df = df.copy()

    # ---------------------------------------------
    # Make sure Ridership is numeric
    # ---------------------------------------------

    analytics_df["Ridership"] = (
        analytics_df["Ridership"]
        .astype(float)
    )

    # ---------------------------------------------
    # Make sure Hour is numeric
    # ---------------------------------------------

    analytics_df["Hour"] = (
        analytics_df["Hour"]
        .astype(int)
    )

    # ---------------------------------------------
    # 1. Hour-wise average ridership
    # ---------------------------------------------

    hourly_data = (
        analytics_df
        .groupby("Hour")["Ridership"]
        .mean()
        .round(2)
        .reset_index()
    )

    hourly_ridership = []

    for _, row in hourly_data.iterrows():

        hourly_ridership.append({
            "Hour": int(row["Hour"]),
            "Ridership": float(row["Ridership"])
        })

    # ---------------------------------------------
    # 2. Station-wise average ridership
    # ---------------------------------------------

    station_data = (
        analytics_df
        .groupby("Station")["Ridership"]
        .mean()
        .round(2)
        .sort_values(
            ascending=False
        )
        .reset_index()
    )

    station_ridership = []

    for _, row in station_data.iterrows():

        station_ridership.append({
            "Station": str(row["Station"]),
            "Ridership": float(row["Ridership"])
        })

    # ---------------------------------------------
    # 3. Find peak hour
    # ---------------------------------------------

    peak_data = (
        analytics_df
        .groupby("Hour")["Ridership"]
        .mean()
        .sort_values(
            ascending=False
        )
    )

    peak_hour = int(
        peak_data.index[0]
    )

    peak_ridership = float(
        round(
            peak_data.iloc[0],
            2
        )
    )

    # ---------------------------------------------
    # Return analytics
    # ---------------------------------------------

    return {
        "hourly_ridership": hourly_ridership,
        "station_ridership": station_ridership,
        "peak_hour": peak_hour,
        "peak_ridership": peak_ridership
    }


# =====================================================
# SCHEDULE OPTIMIZATION API
# =====================================================

@app.post("/schedule")
def schedule(data: PredictionRequest):

    station = data.station
    hour = data.hour

    # ---------------------------------------------
    # Check whether station exists
    # ---------------------------------------------

    if station not in df["Station"].unique():

        return {
            "error": "Station not found"
        }

    # ---------------------------------------------
    # Get station code
    # ---------------------------------------------

    station_code = df.loc[
        df["Station"] == station,
        "station_code"
    ].iloc[0]

    # ---------------------------------------------
    # Get latest date
    # ---------------------------------------------

    latest_date = df["Date"].max()

    year = latest_date.year
    month = latest_date.month
    day = latest_date.day
    day_of_week = latest_date.dayofweek

    # ---------------------------------------------
    # Create model input
    # ---------------------------------------------

    input_data = [[
        hour,
        year,
        month,
        day,
        day_of_week,
        station_code
    ]]

    # ---------------------------------------------
    # Predict ridership
    # ---------------------------------------------

    predicted_ridership = model.predict(input_data)[0]

    predicted_ridership = round(
        float(predicted_ridership),
        2
    )

    # ---------------------------------------------
    # Determine crowd level
    # ---------------------------------------------

    crowd_level = get_crowd_level(
        predicted_ridership
    )

    # ---------------------------------------------
    # Schedule recommendation
    # ---------------------------------------------

    if crowd_level == "HIGH":

        recommended_frequency = "Every 5 minutes"

        action = (
            "Increase train frequency"
        )

    elif crowd_level == "MEDIUM":

        recommended_frequency = "Every 8 minutes"

        action = (
            "Slightly increase train frequency"
        )

    else:

        recommended_frequency = "Every 12 minutes"

        action = (
            "Maintain normal train frequency"
        )

    # ---------------------------------------------
    # Return schedule recommendation
    # ---------------------------------------------

    return {
        "station": station,
        "hour": hour,
        "predicted_ridership": predicted_ridership,
        "crowd_level": crowd_level,
        "recommended_frequency":
            recommended_frequency,
        "action": action
    }