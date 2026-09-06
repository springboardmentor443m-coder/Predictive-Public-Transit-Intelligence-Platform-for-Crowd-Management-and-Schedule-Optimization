import os
import pandas as pd

from flask import (
    Flask,
    jsonify,
    request,
    send_from_directory
)


# ============================================================
# PATH CONFIGURATION
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

FRONTEND_DIR = os.path.join(
    BASE_DIR,
    "frontend"
)

CROWD_FILE = os.path.join(
    BASE_DIR,
    "data",
    "crowd",
    "crowd_management_features.csv"
)

OPTIMIZATION_FILE = os.path.join(
    BASE_DIR,
    "data",
    "optimization",
    "schedule_optimization_recommendations.csv"
)

STOP_OPTIMIZATION_FILE = os.path.join(
    BASE_DIR,
    "data",
    "optimization",
    "stop_optimization_recommendations.csv"
)


# ============================================================
# FLASK APPLICATION
# ============================================================

app = Flask(
    __name__,
    static_folder=FRONTEND_DIR,
    static_url_path=""
)


# ============================================================
# DATA LOADING
# ============================================================

def load_csv(path):

    if not os.path.exists(path):
        return None

    try:
        return pd.read_csv(path)

    except Exception as error:
        print(f"Error loading {path}: {error}")
        return None


crowd_df = load_csv(CROWD_FILE)

optimization_df = load_csv(
    OPTIMIZATION_FILE
)

stop_optimization_df = load_csv(
    STOP_OPTIMIZATION_FILE
)


# ============================================================
# FRONTEND
# ============================================================

@app.route("/")
def frontend():

    return send_from_directory(
        FRONTEND_DIR,
        "index.html"
    )


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/api/health")
def health():

    return jsonify({

        "status": "healthy",

        "crowd_data_available":
            crowd_df is not None,

        "optimization_data_available":
            optimization_df is not None,

        "stop_optimization_available":
            stop_optimization_df is not None,

        "delay_model_status":
            "WAITING_FOR_REAL_DELAY_DATA"
    })


# ============================================================
# SUMMARY
# ============================================================

@app.route("/api/summary")
def summary():

    if crowd_df is None:

        return jsonify({
            "error": "Crowd dataset not found."
        }), 500

    return jsonify({

        "feature_observations":
            int(len(crowd_df)),

        "routes":
            int(crowd_df["route_id"].nunique()),

        "stops":
            int(crowd_df["stop_id"].nunique()),

        "trips":
            int(crowd_df["trip_id"].nunique())
    })


# ============================================================
# ROUTES
# ============================================================

@app.route("/api/routes")
def routes():

    if crowd_df is None:

        return jsonify({
            "error": "Crowd dataset not found."
        }), 500

    columns = [
        "route_id",
        "route_service_category",
        "route_trip_count",
        "route_travel_intensity"
    ]

    available_columns = [
        column
        for column in columns
        if column in crowd_df.columns
    ]

    result = (
        crowd_df[available_columns]
        .drop_duplicates(
            subset=["route_id"]
        )
        .sort_values("route_id")
    )

    return jsonify(
        result.to_dict(
            orient="records"
        )
    )


# ============================================================
# STOPS
# ============================================================

@app.route("/api/stops")
def stops():

    if crowd_df is None:

        return jsonify({
            "error": "Crowd dataset not found."
        }), 500

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

    available_columns = [
        column
        for column in columns
        if column in crowd_df.columns
    ]

    result = (
        crowd_df[available_columns]
        .drop_duplicates(
            subset=[
                "route_id",
                "stop_id"
            ]
        )
    )

    if "stop_name" in result.columns:

        result = result.sort_values(
            ["route_id", "stop_name"]
        )

    else:

        result = result.sort_values(
            ["route_id", "stop_id"]
        )

    return jsonify(
        result.to_dict(
            orient="records"
        )
    )


# ============================================================
# ROUTE DETAILS
# ============================================================

@app.route("/api/route/<path:route_id>")
def route_details(route_id):

    if crowd_df is None:

        return jsonify({
            "error": "Crowd dataset not found."
        }), 500

    route_df = crowd_df[
        crowd_df["route_id"] == route_id
    ]

    if route_df.empty:

        return jsonify({
            "error": "Route not found.",
            "route_id": route_id
        }), 404

    response = {

        "route_id":
            route_id,

        "trips":
            int(route_df["trip_id"].nunique()),

        "stops":
            int(route_df["stop_id"].nunique())
    }

    if "service_pressure_score" in route_df.columns:

        response["service_pressure"] = float(
            route_df[
                "service_pressure_score"
            ].mean()
        )

    if "route_travel_intensity" in route_df.columns:

        response["route_travel_intensity"] = float(
            route_df[
                "route_travel_intensity"
            ].mean()
        )

    if "peak_period" in route_df.columns:

        response["peak_periods"] = (
            route_df["peak_period"]
            .value_counts()
            .to_dict()
        )

    return jsonify(response)


# ============================================================
# CROWD MANAGEMENT
# ============================================================

@app.route("/api/crowd")
def crowd():

    if crowd_df is None:

        return jsonify({
            "error": "Crowd dataset not found."
        }), 500

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

    available_columns = [
        column
        for column in columns
        if column in crowd_df.columns
    ]

    result = crowd_df[
        available_columns
    ].copy()

    route_id = request.args.get(
        "route_id"
    )

    if route_id and "route_id" in result.columns:

        result = result[
            result["route_id"] == route_id
        ]

    hour = request.args.get(
        "hour"
    )

    if hour:

        try:

            hour = int(hour)

            if "scheduled_hour" in result.columns:

                result = result[
                    result["scheduled_hour"] == hour
                ]

        except ValueError:

            return jsonify({
                "error": "Hour must be an integer."
            }), 400

    result = result.head(500)

    return jsonify(
        result.to_dict(
            orient="records"
        )
    )


# ============================================================
# SCHEDULE OPTIMIZATION
# ============================================================

@app.route("/api/optimization")
def optimization():

    if optimization_df is None:

        return jsonify({
            "error":
                "Schedule optimization dataset not found."
        }), 500

    result = optimization_df.copy()

    route_id = request.args.get(
        "route_id"
    )

    if (
        route_id
        and "route_id" in result.columns
    ):

        result = result[
            result["route_id"] == route_id
        ]

    recommendation = request.args.get(
        "recommendation"
    )

    if (
        recommendation
        and "recommendation" in result.columns
    ):

        result = result[
            result["recommendation"]
            == recommendation
        ]

    if (
        "average_service_pressure"
        in result.columns
    ):

        result = result.sort_values(
            "average_service_pressure",
            ascending=False
        )

    result = result.head(500)

    return jsonify(
        result.to_dict(
            orient="records"
        )
    )


# ============================================================
# PRIORITY STATIONS
# ============================================================

@app.route("/api/priority-stops")
def priority_stops():

    if stop_optimization_df is None:

        return jsonify({
            "error":
                "Stop optimization dataset not found."
        }), 500

    result = stop_optimization_df.copy()

    if "stop_recommendation" in result.columns:

        priority = result[
            result["stop_recommendation"]
            == "PRIORITY_STOP_FOR_MONITORING"
        ]

        if not priority.empty:

            result = priority

    if (
        "average_service_pressure"
        in result.columns
    ):

        result = result.sort_values(
            "average_service_pressure",
            ascending=False
        )

    result = result.head(100)

    return jsonify(
        result.to_dict(
            orient="records"
        )
    )


# ============================================================
# DELAY MODEL
# ============================================================

@app.route("/api/delay-model")
def delay_model():

    model_file = os.path.join(
        BASE_DIR,
        "models",
        "historical_delay_target.csv"
    )

    trained_model = os.path.join(
        BASE_DIR,
        "models",
        "delay_prediction_model.joblib"
    )

    return jsonify({

        "status":
            "TRAINED"
            if os.path.exists(trained_model)
            else "WAITING_FOR_REAL_DELAY_DATA",

        "historical_delay_target_available":
            os.path.exists(model_file),

        "trained_model_available":
            os.path.exists(trained_model),

        "artificial_labels_used":
            False
    })


# ============================================================
# SERVER
# ============================================================

if __name__ == "__main__":

    print("=" * 65)

    print(
        "V/LINE TRANSIT INTELLIGENCE BACKEND"
    )

    print("=" * 65)

    print(
        "\nCrowd data:",
        "AVAILABLE"
        if crowd_df is not None
        else "MISSING"
    )

    print(
        "Optimization data:",
        "AVAILABLE"
        if optimization_df is not None
        else "MISSING"
    )

    print(
        "Stop optimization:",
        "AVAILABLE"
        if stop_optimization_df is not None
        else "MISSING"
    )

    print(
        "Delay model: "
        "WAITING FOR REAL DELAY DATA"
    )

    print(
        "\nStarting Flask server..."
    )

    print(
        "Dashboard URL: "
        "http://127.0.0.1:5000/"
    )

    print(
        "Backend URL: "
        "http://127.0.0.1:5000"
    )

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False
    )