import os
import pandas as pd
from flask import Flask, jsonify, request


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
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

app = Flask(__name__)


# ============================================================
# DATA LOADING
# ============================================================

def load_csv(path):

    if not os.path.exists(path):
        return None

    return pd.read_csv(path)


crowd_df = load_csv(CROWD_FILE)
optimization_df = load_csv(OPTIMIZATION_FILE)
stop_optimization_df = load_csv(STOP_OPTIMIZATION_FILE)


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/")
def home():

    return jsonify({
        "project": "Predictive Public Transit Intelligence Platform",
        "status": "running",
        "service": "V/Line Transit Intelligence Backend"
    })


@app.route("/api/health")
def health():

    return jsonify({
        "status": "healthy",
        "crowd_data_available": crowd_df is not None,
        "optimization_data_available": optimization_df is not None,
        "stop_optimization_available": (
            stop_optimization_df is not None
        ),
        "delay_model_status": "WAITING_FOR_REAL_DELAY_DATA"
    })


# ============================================================
# PROJECT SUMMARY
# ============================================================

@app.route("/api/summary")
def summary():

    if crowd_df is None:

        return jsonify({
            "error": "Crowd-management dataset not found."
        }), 500

    return jsonify({
        "feature_observations": int(len(crowd_df)),
        "routes": int(
            crowd_df["route_id"].nunique()
        ),
        "stops": int(
            crowd_df["stop_id"].nunique()
        ),
        "trips": int(
            crowd_df["trip_id"].nunique()
        )
    })


# ============================================================
# ROUTES
# ============================================================

@app.route("/api/routes")
def routes():

    if crowd_df is None:

        return jsonify({
            "error": "Crowd-management dataset not found."
        }), 500

    routes = (
        crowd_df[
            [
                "route_id",
                "route_service_category",
                "route_trip_count",
                "route_travel_intensity"
            ]
        ]
        .drop_duplicates(
            subset=["route_id"]
        )
        .sort_values("route_id")
    )

    return jsonify(
        routes.to_dict(orient="records")
    )


# ============================================================
# STOPS
# ============================================================

@app.route("/api/stops")
def stops():

    if crowd_df is None:

        return jsonify({
            "error": "Crowd-management dataset not found."
        }), 500

    stops_df = (
        crowd_df[
            [
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
        ]
        .drop_duplicates(
            subset=[
                "route_id",
                "stop_id"
            ]
        )
        .sort_values(
            ["route_id", "stop_name"]
        )
    )

    return jsonify(
        stops_df.to_dict(
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
            "error": "Crowd-management dataset not found."
        }), 500

    route_df = crowd_df[
        crowd_df["route_id"] == route_id
    ]

    if route_df.empty:

        return jsonify({
            "error": "Route not found.",
            "route_id": route_id
        }), 404

    return jsonify({
        "route_id": route_id,
        "trips": int(
            route_df["trip_id"].nunique()
        ),
        "stops": int(
            route_df["stop_id"].nunique()
        ),
        "service_pressure": float(
            route_df[
                "service_pressure_score"
            ].mean()
        ),
        "route_travel_intensity": float(
            route_df[
                "route_travel_intensity"
            ].mean()
        ),
        "peak_periods": (
            route_df["peak_period"]
            .value_counts()
            .to_dict()
        )
    })


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

    result = crowd_df[columns].copy()

    # Optional route filter
    route_id = request.args.get(
        "route_id"
    )

    if route_id:

        result = result[
            result["route_id"] == route_id
        ]

    # Optional hour filter
    hour = request.args.get(
        "hour"
    )

    if hour:

        try:
            hour = int(hour)

            result = result[
                result["scheduled_hour"] == hour
            ]

        except ValueError:

            return jsonify({
                "error": "Hour must be an integer."
            }), 400

    # Limit response size
    result = result.head(500)

    return jsonify(
        result.to_dict(
            orient="records"
        )
    )


# ============================================================
# OPTIMIZATION RECOMMENDATIONS
# ============================================================

@app.route("/api/optimization")
def optimization():

    if optimization_df is None:

        return jsonify({
            "error": (
                "Schedule optimization dataset "
                "not found."
            )
        }), 500

    result = optimization_df.copy()

    route_id = request.args.get(
        "route_id"
    )

    if route_id:

        result = result[
            result["route_id"] == route_id
        ]

    recommendation = request.args.get(
        "recommendation"
    )

    if recommendation:

        result = result[
            result["recommendation"]
            == recommendation
        ]

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
# PRIORITY STOPS
# ============================================================

@app.route("/api/priority-stops")
def priority_stops():

    if stop_optimization_df is None:

        return jsonify({
            "error": (
                "Stop optimization dataset "
                "not found."
            )
        }), 500

    result = stop_optimization_df[
        stop_optimization_df[
            "stop_recommendation"
        ] == "PRIORITY_STOP_FOR_MONITORING"
    ].copy()

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
# DELAY MODEL STATUS
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
        "status": (
            "TRAINED"
            if os.path.exists(trained_model)
            else "WAITING_FOR_REAL_DELAY_DATA"
        ),
        "historical_delay_target_available":
            os.path.exists(model_file),
        "trained_model_available":
            os.path.exists(trained_model),
        "artificial_labels_used": False
    })


# ============================================================
# ERROR HANDLER
# ============================================================

@app.errorhandler(404)
def not_found(error):

    return jsonify({
        "error": "API endpoint not found."
    }), 404


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":

    print("=" * 65)
    print("V/LINE TRANSIT INTELLIGENCE BACKEND")
    print("=" * 65)

    print("\nCrowd data:",
          "AVAILABLE" if crowd_df is not None else "MISSING")

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
        "Delay model: WAITING FOR REAL DELAY DATA"
    )

    print("\nStarting Flask server...")
    print("Backend URL: http://127.0.0.1:5000")

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False
    )