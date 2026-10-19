
import logging
import time

from app.services.monitoring_service import (
    get_station_monitoring,
    get_network_monitoring,
)

from app.services.alert_service import (
    generate_station_alerts,
    generate_network_alerts,
)

from app.services.scheduling_intelligence_service import (
    get_station_scheduling_recommendation,
    get_network_scheduling_recommendations,
)

logger = logging.getLogger(__name__)


# STATION OPERATIONS

def get_station_operations_summary(
    station,
    selected_date=None,
    selected_hour=None,
):
    """Combine station monitoring, alerts, and scheduling."""

    total_start = time.perf_counter()

    start = time.perf_counter()
    monitoring = get_station_monitoring(
        station=station,
        selected_date=selected_date,
        selected_hour=selected_hour,
    )

    logger.warning(
        "TIMING station monitoring: %.3f seconds",
        time.perf_counter() - start,
    )

    if monitoring is None:
        return None

    start = time.perf_counter()
    alerts = generate_station_alerts(
        station=station,
        selected_date=selected_date,
        selected_hour=selected_hour,
    )

    logger.warning(
        "TIMING station alerts: %.3f seconds",
        time.perf_counter() - start,
    )

    start = time.perf_counter()
    scheduling = get_station_scheduling_recommendation(station)

    logger.warning(
        "TIMING station scheduling: %.3f seconds",
        time.perf_counter() - start,
    )

    result = {
        "station": station,
        "monitoring": monitoring,
        "alerts": alerts,
        "scheduling": scheduling,
        "assessment_type": (
            "historical-demand-operations-decision-support"
        ),
    }

    logger.warning(
        "TIMING total station operations: %.3f seconds",
        time.perf_counter() - total_start,
    )

    return result


# NETWORK OPERATIONS

def get_network_operations_summary(
    selected_date=None,
    selected_hour=None,
):
    """Combine network monitoring, alerts, and scheduling."""

    total_start = time.perf_counter()

    start = time.perf_counter()
    monitoring = get_network_monitoring(
        selected_date=selected_date,
        selected_hour=selected_hour,
    )

    logger.warning(
        "TIMING network monitoring: %.3f seconds",
        time.perf_counter() - start,
    )

    if monitoring is None:
        monitoring = {}

    start = time.perf_counter()
    alerts = generate_network_alerts(
        network_data=monitoring,
        selected_date=selected_date,
        selected_hour=selected_hour,
    )

    logger.warning(
        "TIMING network alerts: %.3f seconds",
        time.perf_counter() - start,
    )

    start = time.perf_counter()
    scheduling = get_network_scheduling_recommendations()

    logger.warning(
        "TIMING network scheduling: %.3f seconds",
        time.perf_counter() - start,
    )

    station_snapshots = monitoring.get("station_snapshots", [])

    pressure_counts = {
        "LOW": 0,
        "MODERATE": 0,
        "HIGH": 0,
        "CRITICAL": 0,
    }

    for station_data in station_snapshots:
        level = station_data.get("congestion_level")
        if level in pressure_counts:
            pressure_counts[level] += 1

    high_pressure_stations = [
        {
            "station": station_data.get("station"),
            "pressure_score": station_data.get("pressure_score"),
            "congestion_level": station_data.get("congestion_level"),
            "current_ridership": station_data.get("current_ridership"),
            "predicted_next_hour_ridership": station_data.get(
                "predicted_next_hour_ridership"
            ),
        }
        for station_data in station_snapshots
        if (station_data.get("pressure_score") or 0) >= 60
    ]

    highest_ridership = (
        max(
            station_snapshots,
            key=lambda station_data: (
                station_data.get("current_ridership") or 0
            ),
        )
        if station_snapshots
        else None
    )

    result = {
        "monitoring": monitoring,
        "stations_monitored": len(station_snapshots),
        "monitoring_date": monitoring.get("monitoring_date"),
        "monitoring_hour": monitoring.get("monitoring_hour"),
        "pressure_counts": pressure_counts,
        "high_pressure_stations": len(high_pressure_stations),
        "highest_current_ridership": highest_ridership,
        "high_pressure_station_list": high_pressure_stations,
        "alerts": alerts,
        "scheduling": scheduling,
        "assessment_type": (
            "historical-demand-operations-decision-support"
        ),
    }

    logger.warning(
        "TIMING total network operations service: %.3f seconds",
        time.perf_counter() - total_start,
    )

    return result