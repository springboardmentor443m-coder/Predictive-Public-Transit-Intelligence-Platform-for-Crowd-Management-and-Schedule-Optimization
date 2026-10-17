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

MIN_RECOMMENDED_HEADWAY = 4.0
MAX_RECOMMENDED_HEADWAY = 20.0


# ============================================================
# DATA LOADING
# ============================================================

def load_scheduling_intelligence_data():
    """
    Load station scheduling analysis and GTFS data.
    GTFS files are comma-separated text files.
    """

    required_paths = [
        SCHEDULING_DATA_PATH,
        FREQUENCIES_PATH,
        TRIPS_PATH,
        ROUTES_PATH,
    ]

    for path in required_paths:
        if not path.exists():
            raise FileNotFoundError(
                f"Required scheduling data file not found: {path}"
            )

    station_analysis = pd.read_csv(SCHEDULING_DATA_PATH)
    frequencies = pd.read_csv(FREQUENCIES_PATH)
    trips = pd.read_csv(TRIPS_PATH)
    routes = pd.read_csv(ROUTES_PATH)

    required_station_columns = [
        "Station",
        "Scheduling_Priority_Score",
        "Peak_Median_Headway",
        "Peak_Demand_per_Headway",
        "Demand_Intensity",
        "Service_Gap_Ratio",
        "Demand_Concentration",
    ]

    missing_columns = [
        column
        for column in required_station_columns
        if column not in station_analysis.columns
    ]

    if missing_columns:
        raise ValueError(
            "Scheduling analysis is missing required columns: "
            + ", ".join(missing_columns)
        )

    required_frequency_columns = [
        "trip_id",
        "headway_secs",
    ]

    missing_frequency_columns = [
        column
        for column in required_frequency_columns
        if column not in frequencies.columns
    ]

    if missing_frequency_columns:
        raise ValueError(
            "GTFS frequencies file is missing required columns: "
            + ", ".join(missing_frequency_columns)
        )

    required_trip_columns = ["trip_id", "route_id"]

    missing_trip_columns = [
        column
        for column in required_trip_columns
        if column not in trips.columns
    ]

    if missing_trip_columns:
        raise ValueError(
            "GTFS trips file is missing required columns: "
            + ", ".join(missing_trip_columns)
        )

    required_route_columns = [
        "route_id",
        "route_short_name",
        "route_long_name",
    ]

    missing_route_columns = [
        column
        for column in required_route_columns
        if column not in routes.columns
    ]

    if missing_route_columns:
        raise ValueError(
            "GTFS routes file is missing required columns: "
            + ", ".join(missing_route_columns)
        )

    # Convert GTFS headway seconds into minutes.
    frequencies["headway_minutes"] = (
        pd.to_numeric(
            frequencies["headway_secs"],
            errors="coerce",
        )
        / 60.0
    )

    # Validate station-level numerical inputs.
    numeric_columns = [
        "Scheduling_Priority_Score",
        "Peak_Median_Headway",
        "Peak_Demand_per_Headway",
        "Demand_Intensity",
        "Service_Gap_Ratio",
        "Demand_Concentration",
    ]

    for column in numeric_columns:
        station_analysis[column] = pd.to_numeric(
            station_analysis[column],
            errors="coerce",
        )

    station_analysis = station_analysis.dropna(
        subset=["Station"] + numeric_columns
    ).copy()

    station_analysis["Station"] = (
        station_analysis["Station"].astype(str).str.strip()
    )

    station_analysis = station_analysis[
        station_analysis["Station"] != ""
    ].copy()

    if station_analysis.empty:
        raise ValueError(
            "No valid station scheduling records are available."
        )

    if (station_analysis["Peak_Median_Headway"] <= 0).any():
        raise ValueError(
            "Current station headways must be greater than zero."
        )

    if frequencies["headway_minutes"].dropna().empty:
        raise ValueError(
            "No valid GTFS headway values are available."
        )

    return {
        "station_analysis": station_analysis,
        "frequencies": frequencies,
        "trips": trips,
        "routes": routes,
    }


# ============================================================
# PRIORITY CLASSIFICATION
# ============================================================

def classify_priority(priority_score):
    """
    Classify station scheduling priority.
    """

    priority_score = float(priority_score)

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
    priority_level,
    priority_score=None,
):
    """
    Calculate an analytical recommended peak headway.

    This is a planning heuristic, not an operational command.

    HIGH:
        10% base reduction plus up to 10% based on score.

    MODERATE:
        5% base reduction plus up to 5% based on score.

    LOW:
        Maintain the current headway.

    Recommendations are bounded by the configured minimum
    and maximum. Operational feasibility must be assessed
    separately before adopting any recommendation.
    """

    current_headway = float(current_headway)

    if current_headway <= 0:
        raise ValueError(
            "Current headway must be greater than zero."
        )

    if priority_level == "HIGH":
        base_reduction = 0.10
        max_additional_reduction = 0.10
        score_floor = HIGH_PRIORITY_THRESHOLD
        score_ceiling = 1.0

    elif priority_level == "MODERATE":
        base_reduction = 0.05
        max_additional_reduction = 0.05
        score_floor = MEDIUM_PRIORITY_THRESHOLD
        score_ceiling = HIGH_PRIORITY_THRESHOLD

    else:
        base_reduction = 0.0
        max_additional_reduction = 0.0
        score_floor = 0.0
        score_ceiling = MEDIUM_PRIORITY_THRESHOLD

    if (
        priority_score is None
        or max_additional_reduction == 0
    ):
        reduction = base_reduction

    else:
        score_range = score_ceiling - score_floor

        if score_range <= 0:
            normalized_score = 0.0
        else:
            normalized_score = (
                (float(priority_score) - score_floor)
                / score_range
            )

            normalized_score = max(
                0.0,
                min(1.0, normalized_score),
            )

        reduction = (
            base_reduction
            + max_additional_reduction * normalized_score
        )

    recommended = current_headway * (1.0 - reduction)

    recommended = max(
        MIN_RECOMMENDED_HEADWAY,
        recommended,
    )

    recommended = min(
        MAX_RECOMMENDED_HEADWAY,
        recommended,
    )

    return round(recommended, 1)


# ============================================================
# GTFS HEADWAY ANALYSIS
# ============================================================

def get_gtfs_headway_summary():
    """
    Generate route-level headway statistics from GTFS data.

    These statistics describe the supplied GTFS schedule.
    They are not live service measurements.
    """

    data = load_scheduling_intelligence_data()

    frequencies = data["frequencies"]
    trips = data["trips"]
    routes = data["routes"]

    route_trip_map = trips[
        ["trip_id", "route_id"]
    ].drop_duplicates()

    gtfs_schedule = frequencies.merge(
        route_trip_map,
        on="trip_id",
        how="left",
    )

    gtfs_schedule = gtfs_schedule.dropna(
        subset=["route_id", "headway_minutes"]
    )

    if gtfs_schedule.empty:
        raise ValueError(
            "No GTFS frequency records could be linked to routes."
        )

    route_summary = (
        gtfs_schedule
        .groupby("route_id")
        .agg(
            min_headway_minutes=(
                "headway_minutes",
                "min",
            ),
            median_headway_minutes=(
                "headway_minutes",
                "median",
            ),
            max_headway_minutes=(
                "headway_minutes",
                "max",
            ),
            schedule_records=(
                "headway_minutes",
                "count",
            ),
        )
        .reset_index()
    )

    route_summary = route_summary.merge(
        routes[
            [
                "route_id",
                "route_short_name",
                "route_long_name",
            ]
        ].drop_duplicates(subset=["route_id"]),
        on="route_id",
        how="left",
    )

    return route_summary


# ============================================================
# GTFS NETWORK CONTEXT
# ============================================================

def get_gtfs_network_context():
    """
    Calculate network-level GTFS headway statistics once
    per request.
    """

    gtfs_summary = get_gtfs_headway_summary()

    return {
        "gtfs_network_min_headway_minutes": round(
            float(gtfs_summary["min_headway_minutes"].min()),
            1,
        ),
        "gtfs_network_median_headway_minutes": round(
            float(gtfs_summary["median_headway_minutes"].median()),
            1,
        ),
        "gtfs_network_max_headway_minutes": round(
            float(gtfs_summary["max_headway_minutes"].max()),
            1,
        ),
    }


# ============================================================
# STATION-LEVEL SCHEDULING RECOMMENDATION
# ============================================================

def get_station_scheduling_recommendation(station):
    """
    Generate an analytical scheduling recommendation
    for one station.
    """

    data = load_scheduling_intelligence_data()

    station_analysis = data["station_analysis"]

    station_name = str(station).strip()

    station_data = station_analysis[
        station_analysis["Station"].str.casefold()
        == station_name.casefold()
    ]

    if station_data.empty:
        return None

    row = station_data.iloc[0]

    priority_score = float(
        row["Scheduling_Priority_Score"]
    )

    priority_level = classify_priority(
        priority_score
    )

    current_headway = float(
        row["Peak_Median_Headway"]
    )

    recommended_headway = calculate_recommended_headway(
        current_headway,
        priority_level,
        priority_score,
    )

    gtfs_context = get_gtfs_network_context()

    if priority_level == "HIGH":
        action = "Increase peak service frequency"

    elif priority_level == "MODERATE":
        action = (
            "Consider a moderate increase in peak service"
        )

    else:
        action = "Maintain current peak service pattern"

    return {
        "station": row["Station"],
        "priority_level": priority_level,
        "scheduling_priority_score": round(
            priority_score,
            3,
        ),
        "current_peak_median_headway_minutes": round(
            current_headway,
            1,
        ),
        "recommended_peak_headway_minutes": (
            recommended_headway
        ),
        **gtfs_context,
        "peak_demand_per_headway": round(
            float(row["Peak_Demand_per_Headway"]),
            2,
        ),
        "demand_intensity": round(
            float(row["Demand_Intensity"]),
            3,
        ),
        "service_gap_ratio": round(
            float(row["Service_Gap_Ratio"]),
            3,
        ),
        "demand_concentration": round(
            float(row["Demand_Concentration"]),
            3,
        ),
        "action": action,
        "assessment_type": (
            "analytical_scheduling_recommendation"
        ),
    }


# ============================================================
# NETWORK-LEVEL SCHEDULING RECOMMENDATIONS
# ============================================================

def get_network_scheduling_recommendations():
    """
    Generate analytical scheduling recommendations
    for all stations, sorted by priority score.
    """

    data = load_scheduling_intelligence_data()

    station_analysis = data["station_analysis"]

    gtfs_context = get_gtfs_network_context()

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

        recommended_headway = calculate_recommended_headway(
            current_headway,
            priority_level,
            priority_score,
        )

        recommendations.append(
            {
                "station": row["Station"],
                "priority_level": priority_level,
                
                "action": (
                    "Increase peak service frequency"
                    if priority_level == "HIGH"
                    else "Consider a moderate increase in peak service"
                    if priority_level == "MODERATE"
                    else "Maintain current peak service pattern"
                ),

                "scheduling_priority_score": round(
                    priority_score,
                    3,
                ),
                "current_peak_median_headway_minutes": round(
                    current_headway,
                    1,
                ),
                "recommended_peak_headway_minutes": (
                    recommended_headway
                ),
                **gtfs_context,
                "peak_demand_per_headway": round(
                    float(row["Peak_Demand_per_Headway"]),
                    2,
                ),
                "demand_intensity": round(
                    float(row["Demand_Intensity"]),
                    3,
                ),
                "service_gap_ratio": round(
                    float(row["Service_Gap_Ratio"]),
                    3,
                ),
                "demand_concentration": round(
                    float(row["Demand_Concentration"]),
                    3,
                ),
            }
        )

    recommendations.sort(
        key=lambda item: item["scheduling_priority_score"],
        reverse=True,
    )

    return {
        "total_stations": len(recommendations),
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
        ),
    }