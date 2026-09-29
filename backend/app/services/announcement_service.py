def create_announcement(
    title: str,
    message: str,
    severity: str = "medium",
    station: str = "All Stations",
):
    return {
        "announcement": {
            "title": title,
            "message": message,
            "severity": severity,
            "station": station,
            "status": "active",
        }
    }