from datetime import datetime


def generate_analytics(
    total_passengers: int = 0,
    active_alerts: int = 0,
    delayed_trains: int = 0,
    average_delay: float = 0,
    peak_crowd_level: str = "normal",
):
    return {
        "analytics": {
            "total_passengers": total_passengers,
            "active_alerts": active_alerts,
            "delayed_trains": delayed_trains,
            "average_delay_minutes": average_delay,
            "peak_crowd_level": peak_crowd_level,
            "generated_at": datetime.now().isoformat(),
        },
        "status": "available",
    }