from app.services.monitoring_service import (
    get_network_monitoring,
    get_station_monitoring
)


# Alert thresholds
HIGH_PRESSURE_THRESHOLD = 60
CRITICAL_PRESSURE_THRESHOLD = 80
PREDICTION_ERROR_THRESHOLD = 20


def _create_alert(
    station,
    alert_type,
    severity,
    title,
    message,
    recommendation,
    monitoring_data
):
    return {
        "station": station,
        "alert_type": alert_type,
        "severity": severity,
        "title": title,
        "message": message,
        "recommendation": recommendation,
        "monitoring_date": monitoring_data.get("monitoring_date"),
        "monitoring_hour": monitoring_data.get("monitoring_hour"),
        "current_ridership": monitoring_data.get("current_ridership"),
        "predicted_next_hour_ridership": monitoring_data.get(
            "predicted_next_hour_ridership"
        ),
        "observed_next_hour_ridership": monitoring_data.get(
            "observed_next_hour_ridership"
        ),
        "pressure_score": monitoring_data.get("pressure_score"),
        "prediction_error_percentage": monitoring_data.get(
            "prediction_error_percentage"
        ),
        "assessment_type": monitoring_data.get("assessment_type")
    }


def generate_station_alerts(
    station,
    selected_date=None,
    selected_hour=None
):
    """
    Generate operational alerts for a station using
    existing monitoring and prediction results.
    """

    monitoring_data = get_station_monitoring(
        station=station,
        selected_date=selected_date,
        selected_hour=selected_hour
    )

    if monitoring_data is None:
        return {
            "station": station,
            "alerts": [],
            "message": "No monitoring data found."
        }

    alerts = []

    pressure_score = monitoring_data.get("pressure_score", 0)
    prediction_error = monitoring_data.get(
        "prediction_error_percentage",
        0
    )

    # -------------------------------------------------
    # 1. Critical / high crowd-pressure alert
    # -------------------------------------------------

    if pressure_score >= CRITICAL_PRESSURE_THRESHOLD:

        alerts.append(
            _create_alert(
                station=station,
                alert_type="crowd_pressure",
                severity="CRITICAL",
                title="Critical crowd pressure detected",
                message=(
                    f"{station} has a crowd pressure score of "
                    f"{pressure_score:.2f}."
                ),
                recommendation=(
                    "Consider increasing service frequency, "
                    "monitoring platform crowding, and preparing "
                    "station-level crowd management measures."
                ),
                monitoring_data=monitoring_data
            )
        )

    elif pressure_score >= HIGH_PRESSURE_THRESHOLD:

        alerts.append(
            _create_alert(
                station=station,
                alert_type="crowd_pressure",
                severity="HIGH",
                title="High crowd pressure detected",
                message=(
                    f"{station} has a crowd pressure score of "
                    f"{pressure_score:.2f}."
                ),
                recommendation=(
                    "Monitor station crowd conditions and "
                    "consider additional service capacity."
                ),
                monitoring_data=monitoring_data
            )
        )

    # -------------------------------------------------
    # 2. Prediction accuracy alert
    # -------------------------------------------------

    if prediction_error >= PREDICTION_ERROR_THRESHOLD:

        alerts.append(
            _create_alert(
                station=station,
                alert_type="prediction_deviation",
                severity="MODERATE",
                title="Prediction deviation detected",
                message=(
                    f"The predicted ridership differs from the "
                    f"observed next-hour ridership by "
                    f"{prediction_error:.2f}%."
                ),
                recommendation=(
                    "Review recent station demand conditions "
                    "and monitor subsequent predictions."
                ),
                monitoring_data=monitoring_data
            )
        )

    return {
        "station": station,
        "monitoring_date": monitoring_data.get("monitoring_date"),
        "monitoring_hour": monitoring_data.get("monitoring_hour"),
        "alert_count": len(alerts),
        "alerts": alerts,
        "assessment_type": monitoring_data.get(
            "assessment_type"
        )
    }


def generate_network_alerts(
    selected_date=None,
    selected_hour=None
):
    """
    Generate alerts for all monitored stations.
    """

    network_data = get_network_monitoring(
        selected_date=selected_date,
        selected_hour=selected_hour
    )

    station_results = network_data.get(
        "station_snapshots",
        []
    )

    alerts = []

    for station_data in station_results:
        station = station_data.get("station")

        station_alerts = generate_station_alerts(
            station=station,
            selected_date=selected_date,
            selected_hour=selected_hour
        )

        alerts.extend(
            station_alerts.get("alerts", [])
        )

    severity_counts = {
        "CRITICAL": 0,
        "HIGH": 0,
        "MODERATE": 0,
        "LOW": 0
    }

    for alert in alerts:
        severity = alert.get("severity")

        if severity in severity_counts:
            severity_counts[severity] += 1

    return {
        "monitoring_date": network_data.get(
            "monitoring_date"
        ),
        "monitoring_hour": network_data.get(
            "monitoring_hour"
        ),
        "total_alerts": len(alerts),
        "severity_counts": severity_counts,
        "alerts": alerts,
        "assessment_type": (
            "historical-demand-alert-replay"
        )
    }