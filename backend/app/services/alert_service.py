
from app.services.monitoring_service import (
    get_network_monitoring,
    get_station_monitoring,
)

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
    monitoring_data,
):
    alert = {
        "station": station,
        "alert_type": alert_type,
        "severity": severity,
        "title": title,
        "message": message,
        "recommendation": recommendation,
        "monitoring_data": monitoring_data,
    }

    if alert_type == "prediction_deviation":
        alert["prediction_error_percentage"] = (
            monitoring_data.get("prediction_error_percentage", 0) or 0
        )

    return alert


def _summarize_alerts(
    alerts,
    monitoring_date=None,
    monitoring_hour=None,
):
    severity_counts = {
        "CRITICAL": 0,
        "HIGH": 0,
        "MODERATE": 0,
        "LOW": 0,
    }

    for alert in alerts:
        severity = alert.get("severity")
        if severity in severity_counts:
            severity_counts[severity] += 1

    return {
        "monitoring_date": monitoring_date,
        "monitoring_hour": monitoring_hour,
        "total_alerts": len(alerts),
        "alert_count": len(alerts),
        "severity_counts": severity_counts,
        "alerts": alerts,
        "assessment_type": "historical-demand-alert-replay",
    }


def _generate_alerts_for_snapshot(station, monitoring_data):
    alerts = []

    pressure_score = monitoring_data.get("pressure_score", 0) or 0
    prediction_error = (
        monitoring_data.get("prediction_error_percentage", 0) or 0
    )

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
                    "Prioritize station monitoring and consider "
                    "additional service capacity and crowd-management "
                    "measures."
                ),
                monitoring_data=monitoring_data,
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
                    "Monitor station demand and consider additional "
                    "service capacity."
                ),
                monitoring_data=monitoring_data,
            )
        )

    if prediction_error >= PREDICTION_ERROR_THRESHOLD:
        alerts.append(
            _create_alert(
                station=station,
                alert_type="prediction_deviation",
                severity="MODERATE",
                title="Prediction deviation detected",
                message=(
                    "The predicted ridership differs from the "
                    "observed next-hour ridership by "
                    f"{prediction_error:.2f}%."
                ),
                recommendation=(
                    "Review recent station demand conditions and "
                    "monitor subsequent predictions."
                ),
                monitoring_data=monitoring_data,
            )
        )

    return alerts


def generate_station_alerts(
    station,
    selected_date=None,
    selected_hour=None,
):
    monitoring = get_station_monitoring(
        station=station,
        selected_date=selected_date,
        selected_hour=selected_hour,
    )

    if monitoring is None or monitoring.get("data_available") is False:
        result = _summarize_alerts(
            alerts=[],
            monitoring_date=selected_date,
            monitoring_hour=selected_hour,
        )
        result.update({
            "station": station,
            "message": "No monitoring data found.",
        })
        return result

    alerts = _generate_alerts_for_snapshot(
        station=station,
        monitoring_data=monitoring,
    )

    result = _summarize_alerts(
        alerts=alerts,
        monitoring_date=monitoring.get(
            "monitoring_date", selected_date
        ),
        monitoring_hour=monitoring.get(
            "monitoring_hour", selected_hour
        ),
    )

    result["station"] = station
    return result


def generate_network_alerts(
    selected_date=None,
    selected_hour=None,
    network_data=None,
):
    if network_data is None:
        network_data = get_network_monitoring(
            selected_date=selected_date,
            selected_hour=selected_hour,
        )

    if network_data is None:
        return _summarize_alerts(
            alerts=[],
            monitoring_date=selected_date,
            monitoring_hour=selected_hour,
        )

    alerts = []

    for station_data in network_data.get("station_snapshots", []):
        station = station_data.get("station")

        if not station or station_data.get("data_available") is False:
            continue

        alerts.extend(
            _generate_alerts_for_snapshot(
                station=station,
                monitoring_data=station_data,
            )
        )

    return _summarize_alerts(
        alerts=alerts,
        monitoring_date=network_data.get(
            "monitoring_date", selected_date
        ),
        monitoring_hour=network_data.get(
            "monitoring_hour", selected_hour
        ),
    )
