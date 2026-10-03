from app.services.monitoring_service import (
    get_station_monitoring,
    get_network_monitoring
)

from app.services.alert_service import (
    generate_station_alerts,
    generate_network_alerts
)

from app.services.scheduling_intelligence_service import (
    get_station_scheduling_recommendation,
    get_network_scheduling_recommendations
)


def get_station_operations_summary(
    station,
    selected_date=None,
    selected_hour=None
):
    """
    Combine monitoring, alerts, and scheduling intelligence
    into a single station-level operational summary.
    """

    monitoring = get_station_monitoring(
        station=station,
        selected_date=selected_date,
        selected_hour=selected_hour
    )

    if monitoring is None:
        return None

    alerts = generate_station_alerts(
        station=station,
        selected_date=selected_date,
        selected_hour=selected_hour
    )

    scheduling = get_station_scheduling_recommendation(
        station
    )

    return {
        "station": station,

        "monitoring": monitoring,

        "alerts": alerts,

        "scheduling": scheduling,

        "assessment_type": (
            "historical-demand-operations-decision-support"
        )
    }



from app.services.monitoring_service import (
    get_station_monitoring,
    get_network_monitoring
)

from app.services.alert_service import (
    generate_station_alerts,
    generate_network_alerts
)

from app.services.scheduling_intelligence_service import (
    get_station_scheduling_recommendation,
    get_network_scheduling_recommendations
)


def get_station_operations_summary(
    station,
    selected_date=None,
    selected_hour=None
):
    """
    Combine monitoring, alerts, and scheduling intelligence
    into a single station-level operational summary.
    """

    monitoring = get_station_monitoring(
        station=station,
        selected_date=selected_date,
        selected_hour=selected_hour
    )

    if monitoring is None:
        return None

    alerts = generate_station_alerts(
        station=station,
        selected_date=selected_date,
        selected_hour=selected_hour
    )

    scheduling = get_station_scheduling_recommendation(
        station
    )

    return {
        "station": station,

        "monitoring": monitoring,

        "alerts": alerts,

        "scheduling": scheduling,

        "assessment_type": (
            "historical-demand-operations-decision-support"
        )
    }


def get_network_operations_summary(
    selected_date=None,
    selected_hour=None
):
    """
    Combine network monitoring, alerts, and scheduling
    intelligence into a single operational summary.
    """

    monitoring = get_network_monitoring(
        selected_date=selected_date,
        selected_hour=selected_hour
    )

    alerts = generate_network_alerts(
        selected_date=selected_date,
        selected_hour=selected_hour
    )

    scheduling = get_network_scheduling_recommendations()

    station_snapshots = monitoring.get(
        "station_snapshots",
        []
    )

    pressure_counts = {
        "LOW": 0,
        "MODERATE": 0,
        "HIGH": 0,
        "CRITICAL": 0
    }

    for station in station_snapshots:

        pressure_level = station.get(
            "congestion_level"
        )

        if pressure_level in pressure_counts:
            pressure_counts[pressure_level] += 1

    return {
        "monitoring_date": monitoring.get(
            "monitoring_date"
        ),

        "monitoring_hour": monitoring.get(
            "monitoring_hour"
        ),

        "stations_monitored": len(
            station_snapshots
        ),

        "pressure_counts": pressure_counts,

        "monitoring": monitoring,

        "alerts": alerts,

        "scheduling": scheduling,

        "assessment_type": (
            "historical-demand-operations-decision-support"
        )
    }