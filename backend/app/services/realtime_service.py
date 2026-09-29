from datetime import datetime


def get_realtime_update(
    station: str,
    crowd_level: str = "normal",
    train_status: str = "on_time",
    delay_minutes: float = 0,
):
    return {
        "station": station,
        "crowd_level": crowd_level,
        "train_status": train_status,
        "delay_minutes": delay_minutes,
        "last_updated": datetime.now().isoformat(),
        "status": "live",
    }