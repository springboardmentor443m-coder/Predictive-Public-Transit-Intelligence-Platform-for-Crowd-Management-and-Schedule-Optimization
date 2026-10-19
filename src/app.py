
import joblib
import os
import pandas as pd

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS


# ============================================================
# PATH CONFIGURATION
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

CROWD_FILE = os.path.join(
    BASE_DIR, "data", "crowd", "crowd_management_features.csv"
)

OPTIMIZATION_FILE = os.path.join(
    BASE_DIR, "data", "optimization",
    "schedule_optimization_recommendations.csv"
)

STOP_OPTIMIZATION_FILE = os.path.join(
    BASE_DIR, "data", "optimization",
    "stop_optimization_recommendations.csv"
)

HISTORICAL_DELAY_FILE = os.path.join(
    BASE_DIR, "models", "historical_delay_target.csv"
)

DELAY_MODEL_FILE = os.path.join(
    BASE_DIR, "models", "delay_prediction_model.joblib"
)


# ============================================================
# FLASK APPLICATION
# ============================================================

app = Flask(
    __name__,
    static_folder=FRONTEND_DIR,
    static_url_path=""
)

CORS(
    app,
    resources={
        r"/api/*": {
            "origins": [
                "http://localhost:8000",
                "http://127.0.0.1:8000",
                "http://localhost:5000",
                "http://127.0.0.1:5000"
            ]
        }
    }
)


# ============================================================
# DATA LOADING
# ============================================================

def load_csv(path):
    """Load a CSV file safely."""
    if not os.path.isfile(path):
        print(f"Data file not found: {path}")
        return None

    try:
        return pd.read_csv(path)
    except Exception as error:
        print(f"Error loading {path}: {error}")
        return None


crowd_df = load_csv(CROWD_FILE)
optimization_df = load_csv(OPTIMIZATION_FILE)
stop_optimization_df = load_csv(STOP_OPTIMIZATION_FILE)


def file_exists(path):
    return os.path.isfile(path)


def get_delay_model_status():
    """Report model availability without claiming accuracy."""
    if file_exists(DELAY_MODEL_FILE):
        return "TRAINED_PRELIMINARY"

    if file_exists(HISTORICAL_DELAY_FILE):
        return "DATA_AVAILABLE_MODEL_NOT_TRAINED"

    return "WAITING_FOR_REAL_DELAY_DATA"


def dataframe_records(df):
    """Convert DataFrame rows into JSON-safe records."""
    if df is None:
        return []

    clean_df = df.astype(object).where(pd.notna(df), None)
    return clean_df.to_dict(orient="records")


# ============================================================
# FRONTEND
# ============================================================

@app.route("/")
def frontend():
    index_file = os.path.join(FRONTEND_DIR, "index.html")

    if not os.path.isfile(index_file):
        return jsonify({
            "error": "Frontend index.html was not found.",
            "frontend_directory": FRONTEND_DIR
        }), 404

    return send_from_directory(FRONTEND_DIR, "index.html")


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy",
        "crowd_data_available": crowd_df is not None,
        "optimization_data_available": optimization_df is not None,
        "stop_optimization_available": stop_optimization_df is not None,
        "historical_delay_target_available": file_exists(
            HISTORICAL_DELAY_FILE
        ),
        "delay_model_available": file_exists(DELAY_MODEL_FILE),
        "delay_model_status": get_delay_model_status()
    })


# ============================================================
# NETWORK SUMMARY
# ============================================================

@app.route("/api/summary", methods=["GET"])
def summary():
    if crowd_df is None:
        return jsonify({"error": "Crowd dataset not found."}), 500

    required = ["route_id", "stop_id", "trip_id"]
    missing = [
        column for column in required
        if column not in crowd_df.columns
    ]

    if missing:
        return jsonify({
            "error": "Required columns are missing from crowd data.",
            "missing_columns": missing
        }), 500

    return jsonify({
        "feature_observations": int(len(crowd_df)),
        "routes": int(crowd_df["route_id"].nunique()),
        "stops": int(crowd_df["stop_id"].nunique()),
        "trips": int(crowd_df["trip_id"].nunique())
    })


# ============================================================
# ROUTES
# ============================================================

@app.route("/api/routes", methods=["GET"])
def routes():
    if crowd_df is None:
        return jsonify({"error": "Crowd dataset not found."}), 500

    columns = [
        "route_id",
        "route_service_category",
        "route_trip_count",
        "route_travel_intensity"
    ]

    available = [
        column for column in columns
        if column in crowd_df.columns
    ]

    if "route_id" not in available:
        return jsonify({
            "error": "route_id column is missing."
        }), 500

    result = (
        crowd_df[available]
        .drop_duplicates(subset=["route_id"])
        .sort_values("route_id")
    )

    return jsonify(dataframe_records(result))


# ============================================================
# STOPS
# ============================================================

@app.route("/api/stops", methods=["GET"])
def stops():
    if crowd_df is None:
        return jsonify({"error": "Crowd dataset not found."}), 500

    columns = [
        "route_id",
        "stop_id",
        "stop_name",
        "stop_lat",
        "stop_lon",
        "stop_activity_category",
        "stop_service_intensity",
        "service_pressure_score",
        "service_pressure_category"
    ]

    available = [
        column for column in columns
        if column in crowd_df.columns
    ]

    if not all(
        column in available
        for column in ["route_id", "stop_id"]
    ):
        return jsonify({
            "error": "route_id or stop_id column is missing."
        }), 500

    result = crowd_df[available].drop_duplicates(
        subset=["route_id", "stop_id"]
    )

    sort_columns = [
        column
        for column in ["route_id", "stop_name", "stop_id"]
        if column in result.columns
    ]

    if sort_columns:
        result = result.sort_values(sort_columns)

    return jsonify(dataframe_records(result))


# ============================================================
# ROUTE DETAILS
# ============================================================

@app.route("/api/route/<path:route_id>", methods=["GET"])
def route_details(route_id):
    if crowd_df is None:
        return jsonify({"error": "Crowd dataset not found."}), 500

    if "route_id" not in crowd_df.columns:
        return jsonify({
            "error": "route_id column is missing."
        }), 500

    route_df = crowd_df[
        crowd_df["route_id"].astype(str) == route_id
    ]

    if route_df.empty:
        return jsonify({
            "error": "Route not found.",
            "route_id": route_id
        }), 404

    response = {"route_id": route_id}

    if "trip_id" in route_df.columns:
        response["trips"] = int(route_df["trip_id"].nunique())

    if "stop_id" in route_df.columns:
        response["stops"] = int(route_df["stop_id"].nunique())

    if "service_pressure_score" in route_df.columns:
        response["service_pressure"] = float(
            route_df["service_pressure_score"].mean()
        )

    if "route_travel_intensity" in route_df.columns:
        response["route_travel_intensity"] = float(
            route_df["route_travel_intensity"].mean()
        )

    if "peak_period" in route_df.columns:
        response["peak_periods"] = (
            route_df["peak_period"].value_counts().to_dict()
        )

    return jsonify(response)


# ============================================================
# CROWD MANAGEMENT
# ============================================================

@app.route("/api/crowd", methods=["GET"])
def crowd():
    if crowd_df is None:
        return jsonify({"error": "Crowd dataset not found."}), 500

    columns = [
        "route_id",
        "stop_id",
        "stop_name",
        "scheduled_hour",
        "peak_period",
        "hourly_route_trip_frequency",
        "hourly_stop_trip_frequency",
        "service_pressure_score",
        "service_pressure_category",
        "stop_activity_category"
    ]

    available = [
        column for column in columns
        if column in crowd_df.columns
    ]

    result = crowd_df[available].copy()

    route_id = request.args.get("route_id")
    if route_id and "route_id" in result.columns:
        result = result[
            result["route_id"].astype(str) == route_id
        ]

    hour = request.args.get("hour")
    if hour:
        try:
            hour = int(hour)

            if not 0 <= hour <= 23:
                return jsonify({
                    "error": "Hour must be between 0 and 23."
                }), 400

            if "scheduled_hour" in result.columns:
                result = result[
                    result["scheduled_hour"] == hour
                ]

        except ValueError:
            return jsonify({
                "error": "Hour must be an integer."
            }), 400

    return jsonify(dataframe_records(result.head(500)))


# ============================================================
# SCHEDULE OPTIMIZATION
# ============================================================

@app.route("/api/optimization", methods=["GET"])
def optimization():
    if optimization_df is None:
        return jsonify({
            "error": "Schedule optimization dataset not found."
        }), 500

    result = optimization_df.copy()

    route_id = request.args.get("route_id")
    if route_id and "route_id" in result.columns:
        result = result[
            result["route_id"].astype(str) == route_id
        ]

    recommendation = request.args.get("recommendation")
    if recommendation and "recommendation" in result.columns:
        result = result[
            result["recommendation"] == recommendation
        ]

    if "average_service_pressure" in result.columns:
        result = result.sort_values(
            "average_service_pressure",
            ascending=False
        )

    return jsonify(dataframe_records(result.head(500)))


# ============================================================
# PRIORITY STATIONS
# ============================================================

@app.route("/api/priority-stops", methods=["GET"])
def priority_stops():
    """
    Return station recommendations across all categories.

    Do not filter out normal and monitoring stations. The frontend
    can display the original recommendation and pressure category.
    """
    if stop_optimization_df is None:
        return jsonify({
            "error": "Stop optimization dataset not found."
        }), 500

    result = stop_optimization_df.copy()

    if "average_service_pressure" in result.columns:
        result = result.sort_values(
            "average_service_pressure",
            ascending=False
        )

    return jsonify(dataframe_records(result.head(100)))


# ============================================================
# DELAY MODEL AND EXPERIMENTAL STATION ESTIMATES
# ============================================================

@app.route("/api/delay-model", methods=["GET"])
def delay_model():
    """Return model status and experimental estimates for two stations."""

    historical_available = file_exists(HISTORICAL_DELAY_FILE)
    model_available = file_exists(DELAY_MODEL_FILE)

    observation_count = 0
    unique_trip_count = 0
    predictions = []
    prediction_error = None

    history = pd.DataFrame()

    if historical_available:
        try:
            history = pd.read_csv(
                HISTORICAL_DELAY_FILE,
                dtype={"stop_id": str}
            )

            observation_count = int(len(history))

            if "trip_id" in history.columns:
                unique_trip_count = int(
                    history["trip_id"].nunique()
                )

        except Exception as error:
            app.logger.exception(
                "Unable to read historical delay target"
            )

            return jsonify({
                "status": "DATA_READ_ERROR",
                "error": str(error),
                "historical_delay_target_available": True,
                "trained_model_available": model_available,
                "historical_observations": 0,
                "unique_trips": 0,
                "artificial_labels_used": False,
                "prediction_ready_for_operational_use": False,
                "station_predictions": [],
                "prediction_error": str(error),
                "evaluation_note": (
                    "Historical delay data could not be read. "
                    "Operational forecasting is not validated."
                )
            }), 500

    if model_available and not history.empty:
        try:
            model = joblib.load(DELAY_MODEL_FILE)

            stops_path = os.path.join(
                BASE_DIR,
                "data",
                "static",
                "stops.txt"
            )

            if not os.path.isfile(stops_path):
                raise FileNotFoundError(
                    f"GTFS stops file not found: {stops_path}"
                )

            stops_df = pd.read_csv(
                stops_path,
                dtype={"stop_id": str}
            )

            required_columns = [
                "stop_id",
                "trip_id",
                "delay_seconds",
                "scheduled_arrival_time",
                "scheduled_departure_time",
                "stop_sequence"
            ]

            missing_columns = [
                column
                for column in required_columns
                if column not in history.columns
            ]

            if missing_columns:
                raise ValueError(
                    "Historical data is missing columns: "
                    + ", ".join(missing_columns)
                )

            if not hasattr(model, "feature_names_in_"):
                raise ValueError(
                    "The saved model does not expose feature_names_in_. "
                    "Its required inputs could not be verified."
                )

            def time_to_seconds(value):
                """Convert GTFS HH:MM:SS to seconds."""
                if pd.isna(value):
                    return float("nan")

                parts = str(value).strip().split(":")

                if len(parts) != 3:
                    return float("nan")

                try:
                    hours = int(parts[0])
                    minutes = int(parts[1])
                    seconds = float(parts[2])
                except (TypeError, ValueError):
                    return float("nan")

                if hours < 0 or not 0 <= minutes < 60:
                    return float("nan")

                if not 0 <= seconds < 60:
                    return float("nan")

                return hours * 3600 + minutes * 60 + seconds

            station_names = [
                "Footscray Station",
                "Sunshine Station"
            ]

            for station_name in station_names:
                station_ids = stops_df.loc[
                    stops_df["stop_name"].astype(str) == station_name,
                    "stop_id"
                ].astype(str)

                station_rows = history[
                    history["stop_id"].astype(str).isin(station_ids)
                ].copy()

                if station_rows.empty:
                    app.logger.warning(
                        "No historical rows found for %s",
                        station_name
                    )
                    continue

                station_rows["delay_seconds"] = pd.to_numeric(
                    station_rows["delay_seconds"],
                    errors="coerce"
                )

                station_rows["stop_sequence"] = pd.to_numeric(
                    station_rows["stop_sequence"],
                    errors="coerce"
                )

                station_rows = station_rows.dropna(
                    subset=[
                        "delay_seconds",
                        "stop_sequence",
                        "scheduled_arrival_time",
                        "scheduled_departure_time"
                    ]
                )

                if station_rows.empty:
                    continue

                # Use an existing historical schedule row for a
                # demonstration. This is not a live forecast.
                row = station_rows.iloc[[0]].copy()

                row["scheduled_arrival_seconds"] = (
                    row["scheduled_arrival_time"].apply(
                        time_to_seconds
                    )
                )

                row["scheduled_departure_seconds"] = (
                    row["scheduled_departure_time"].apply(
                        time_to_seconds
                    )
                )

                feature_columns = list(model.feature_names_in_)

                missing_features = [
                    column
                    for column in feature_columns
                    if column not in row.columns
                ]

                if missing_features:
                    raise ValueError(
                        "Model input columns are missing: "
                        + ", ".join(missing_features)
                    )

                features = row[feature_columns].copy()

                for column in [
                    "stop_sequence",
                    "scheduled_arrival_seconds",
                    "scheduled_departure_seconds"
                ]:
                    if column in features.columns:
                        features[column] = pd.to_numeric(
                            features[column],
                            errors="coerce"
                        )

                if features.isna().any().any():
                    app.logger.warning(
                        "Skipping %s because required model features "
                        "contain missing values",
                        station_name
                    )
                    continue

                predicted_seconds = float(
                    model.predict(features)[0]
                )

                historical_seconds = float(
                    row.iloc[0]["delay_seconds"]
                )

                predictions.append({
                    "station_name": station_name,
                    "trip_id": str(row.iloc[0]["trip_id"]),
                    "predicted_delay_minutes": round(
                        predicted_seconds / 60.0,
                        2
                    ),
                    "historical_delay_minutes": round(
                        historical_seconds / 60.0,
                        2
                    )
                })

        except Exception as error:
            app.logger.exception(
                "Unable to generate experimental station estimates"
            )
            prediction_error = str(error)

    return jsonify({
        "status": get_delay_model_status(),
        "historical_delay_target_available": (
            historical_available and observation_count > 0
        ),
        "trained_model_available": model_available,
        "historical_observations": observation_count,
        "unique_trips": unique_trip_count,
        "artificial_labels_used": False,
        "prediction_ready_for_operational_use": False,
        "station_predictions": predictions,
        "prediction_error": prediction_error,
        "evaluation_note": (
            "Experimental estimates are generated from historical "
            "schedule-feature rows. They are not live forecasts or "
            "independent accuracy measurements. Further validation "
            "is required."
        )
    })


# ============================================================
# SERVER
# ============================================================

if __name__ == "__main__":
    print("=" * 65)
    print("V/LINE TRANSIT INTELLIGENCE BACKEND")
    print("=" * 65)

    print(
        "\nCrowd data:",
        "AVAILABLE" if crowd_df is not None else "MISSING"
    )

    print(
        "Optimization data:",
        "AVAILABLE" if optimization_df is not None else "MISSING"
    )

    print(
        "Stop optimization:",
        "AVAILABLE" if stop_optimization_df is not None else "MISSING"
    )

    print(
        "Delay model:",
        get_delay_model_status()
    )

    print("\nDashboard URL: http://127.0.0.1:5000/")
    print("Backend URL:   http://127.0.0.1:5000")
    print("=" * 65)

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False
    )
