from pathlib import Path

import pandas as pd


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[3]

SCHEDULING_DATA_PATH = (
    BASE_DIR / "outputs" / "station_scheduling_analysis.csv"
)

FREQUENCIES_PATH = (
    BASE_DIR / "data" / "bmrcl" / "frequencies.txt"
)

TRIPS_PATH = (
    BASE_DIR / "data" / "bmrcl" / "trips.txt"
)

ROUTES_PATH = (
    BASE_DIR / "data" / "bmrcl" / "routes.txt"
)


# ============================================================
# SCHEDULING PARAMETERS
# ============================================================

HIGH_PRIORITY_THRESHOLD = 0.50
MEDIUM_PRIORITY_THRESHOLD = 0.35

HEADWAY_REDUCTION_HIGH = 0.20
HEADWAY_REDUCTION_MEDIUM = 0.10

MIN_RECOMMENDED_HEADWAY = 4.0
MAX_RECOMMENDED_HEADWAY = 20.0


# ============================================================
# DATA LOADING
# ============================================================

def load_scheduling_intelligence_data():
    """
    Load station scheduling analysis and GTFS data.
    """

    station_analysis = pd.read_csv(
        SCHEDULING_DATA_PATH
    )

    frequencies = pd.read_csv(
        FREQUENCIES_PATH
    )

    trips = pd.read_csv(
        TRIPS_PATH
    )

    routes = pd.read_csv(
        ROUTES_PATH
    )

    frequencies["headway_minutes"] = (
        frequencies["headway_secs"] / 60
    )

    return {
        "station_analysis": station_analysis,
        "frequencies": frequencies,
        "trips": trips,
        "routes": routes
    }


# ============================================================
# PRIORITY CLASSIFICATION
# ============================================================

def classify_priority(priority_score):
    """
    Classify station scheduling priority.
    """

    if priority_score >= HIGH_PRIORITY_THRESHOLD:
        return "HIGH"

    if priority_score >= MEDIUM_PRIORITY_THRESHOLD:
        return "MODERATE"

    return "LOW"


# ============================================================
# HEADWAY RECOMMENDATION
# ============================================================

def calculate_recommended_headway(
    current_headway,
    priority_level
):
    """
    Calculate an analytical recommended peak headway.

    Higher scheduling priority results in a shorter
    recommended headway.
    """

    if priority_level == "HIGH":

        recommended = (
            current_headway
            * (1 - HEADWAY_REDUCTION_HIGH)
        )

    elif priority_level == "MODERATE":

        recommended = (
            current_headway
            * (1 - HEADWAY_REDUCTION_MEDIUM)
        )

    else:

        recommended = current_headway

    recommended = max(
        MIN_RECOMMENDED_HEADWAY,
        recommended
    )

    recommended = min(
        MAX_RECOMMENDED_HEADWAY,
        recommended
    )

    return round(recommended, 1)


# ============================================================
# GTFS HEADWAY ANALYSIS
# ============================================================

def get_gtfs_headway_summary():
    """
    Generate route-level headway statistics directly
    from the GTFS schedule data.
    """

    data = load_scheduling_intelligence_data()

    frequencies = data["frequencies"]
    trips = data["trips"]
    routes = data["routes"]

    # Connect each GTFS trip to its route.
    route_trip_map = trips[
        ["trip_id", "route_id"]
    ].drop_duplicates()

    gtfs_schedule = frequencies.merge(
        route_trip_map,
        on="trip_id",
        how="left"
    )

    # Calculate route-level headway statistics.
    route_summary = (
        gtfs_schedule
        .groupby("route_id")
        .agg(
            min_headway_minutes=(
                "headway_minutes",
                "min"
            ),
            median_headway_minutes=(
                "headway_minutes",
                "median"
            ),
            max_headway_minutes=(
                "headway_minutes",
                "max"
            ),
            schedule_records=(
                "headway_minutes",
                "count"
            )
        )
        .reset_index()
    )

    # Add route names.
    route_summary = route_summary.merge(
        routes[
            [
                "route_id",
                "route_short_name",
                "route_long_name"
            ]
        ],
        on="route_id",
        how="left"
    )

    return route_summary


# ============================================================
# STATION-LEVEL SCHEDULING RECOMMENDATION
# ============================================================

def get_station_scheduling_recommendation(station):
    """
    Generate an analytical scheduling recommendation
    for a specific station.
    """

    data = load_scheduling_intelligence_data()

    station_analysis = data["station_analysis"]

    station_data = station_analysis[
        station_analysis["Station"].str.lower()
        == station.lower()
    ]

    if station_data.empty:
        return None

    row = station_data.iloc[0]

    # --------------------------------------------
    # Scheduling priority
    # --------------------------------------------

    priority_score = float(
        row["Scheduling_Priority_Score"]
    )

    priority_level = classify_priority(
        priority_score
    )

    # --------------------------------------------
    # Current and recommended headway
    # --------------------------------------------

    current_headway = float(
        row["Peak_Median_Headway"]
    )

    recommended_headway = (
        calculate_recommended_headway(
            current_headway,
            priority_level
        )
    )

    # --------------------------------------------
    # GTFS network schedule context
    # --------------------------------------------

    gtfs_summary = get_gtfs_headway_summary()

    gtfs_network_min_headway = float(
        gtfs_summary[
            "min_headway_minutes"
        ].min()
    )

    gtfs_network_median_headway = float(
        gtfs_summary[
            "median_headway_minutes"
        ].median()
    )

    gtfs_network_max_headway = float(
        gtfs_summary[
            "max_headway_minutes"
        ].max()
    )

    # --------------------------------------------
    # Recommended action
    # --------------------------------------------

    if priority_level == "HIGH":

        action = (
            "Increase peak service frequency"
        )

    elif priority_level == "MODERATE":

        action = (
            "Consider a moderate increase "
            "in peak service"
        )

    else:

        action = (
            "Maintain current peak service pattern"
        )

    # --------------------------------------------
    # Final response
    # --------------------------------------------

    return {
        "station": row["Station"],

        "priority_level": priority_level,

        "scheduling_priority_score": round(
            priority_score,
            3
        ),

        "current_peak_median_headway_minutes": round(
            current_headway,
            1
        ),

        "recommended_peak_headway_minutes": (
            recommended_headway
        ),

        "gtfs_network_min_headway_minutes": round(
            gtfs_network_min_headway,
            1
        ),

        "gtfs_network_median_headway_minutes": round(
            gtfs_network_median_headway,
            1
        ),

        "gtfs_network_max_headway_minutes": round(
            gtfs_network_max_headway,
            1
        ),

        "peak_demand_per_headway": round(
            float(
                row["Peak_Demand_per_Headway"]
            ),
            2
        ),

        "demand_intensity": round(
            float(
                row["Demand_Intensity"]
            ),
            3
        ),

        "service_gap_ratio": round(
            float(
                row["Service_Gap_Ratio"]
            ),
            3
        ),

        "demand_concentration": round(
            float(
                row["Demand_Concentration"]
            ),
            3
        ),

        "action": action,

        "assessment_type": (
            "analytical_scheduling_recommendation"
        )
    }


# ============================================================
# NETWORK-LEVEL SCHEDULING RECOMMENDATIONS
# ============================================================

def get_network_scheduling_recommendations():
    """
    Generate scheduling recommendations for
    all stations.
    """

    data = load_scheduling_intelligence_data()

    station_analysis = data["station_analysis"]

    # Calculate GTFS network context once.
    # This avoids recalculating it for every station.
    gtfs_summary = get_gtfs_headway_summary()

    gtfs_network_min_headway = float(
        gtfs_summary[
            "min_headway_minutes"
        ].min()
    )

    gtfs_network_median_headway = float(
        gtfs_summary[
            "median_headway_minutes"
        ].median()
    )

    gtfs_network_max_headway = float(
        gtfs_summary[
            "max_headway_minutes"
        ].max()
    )

    recommendations = []

    for _, row in station_analysis.iterrows():

        priority_score = float(
            row["Scheduling_Priority_Score"]
        )

        priority_level = classify_priority(
            priority_score
        )

        current_headway = float(
            row["Peak_Median_Headway"]
        )

        recommended_headway = (
            calculate_recommended_headway(
                current_headway,
                priority_level
            )
        )

        recommendations.append(
            {
                "station": row["Station"],

                "priority_level": priority_level,

                "scheduling_priority_score": round(
                    priority_score,
                    3
                ),

                "current_peak_median_headway_minutes": (
                    round(
                        current_headway,
                        1
                    )
                ),

                "recommended_peak_headway_minutes": (
                    recommended_headway
                ),

                "gtfs_network_min_headway_minutes": (
                    round(
                        gtfs_network_min_headway,
                        1
                    )
                ),

                "gtfs_network_median_headway_minutes": (
                    round(
                        gtfs_network_median_headway,
                        1
                    )
                ),

                "gtfs_network_max_headway_minutes": (
                    round(
                        gtfs_network_max_headway,
                        1
                    )
                ),

                "peak_demand_per_headway": round(
                    float(
                        row["Peak_Demand_per_Headway"]
                    ),
                    2
                ),

                "demand_intensity": round(
                    float(
                        row["Demand_Intensity"]
                    ),
                    3
                ),

                "service_gap_ratio": round(
                    float(
                        row["Service_Gap_Ratio"]
                    ),
                    3
                ),

                "demand_concentration": round(
                    float(
                        row["Demand_Concentration"]
                    ),
                    3
                )
            }
        )

    # Highest scheduling priority first.
    recommendations.sort(
        key=lambda item: (
            item["scheduling_priority_score"]
        ),
        reverse=True
    )

    return {
        "total_stations": len(
            recommendations
        ),

        "high_priority_stations": sum(
            1
            for item in recommendations
            if item["priority_level"] == "HIGH"
        ),

        "moderate_priority_stations": sum(
            1
            for item in recommendations
            if item["priority_level"] == "MODERATE"
        ),

        "low_priority_stations": sum(
            1
            for item in recommendations
            if item["priority_level"] == "LOW"
        ),

        "recommendations": recommendations,

        "assessment_type": (
            "analytical_network_scheduling_recommendation"
        )
    }