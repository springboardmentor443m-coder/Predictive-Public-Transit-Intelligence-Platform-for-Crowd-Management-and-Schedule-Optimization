def generate_alerts(
    predicted_ridership=0,
    traffic_level="normal",
    delay_minutes=0,
):
    alerts = []

    if predicted_ridership >= 500:
        alerts.append({
            "type": "overcrowding",
            "severity": "high",
            "message": "High passenger demand detected. Increase monitoring and train frequency.",
        })

    if traffic_level == "high":
        alerts.append({
            "type": "congestion",
            "severity": "medium",
            "message": "High traffic detected on the monitored route.",
        })

    if delay_minutes > 15:
        alerts.append({
            "type": "delay",
            "severity": "high",
            "message": "Major train delay detected. Activate delay response procedures.",
        })
    elif delay_minutes > 5:
        alerts.append({
            "type": "delay",
            "severity": "medium",
            "message": "Moderate train delay detected. Monitor and adjust operations.",
        })

    if not alerts:
        alerts.append({
            "type": "system",
            "severity": "low",
            "message": "No critical operating alerts detected.",
        })

    return {
        "alert_count": len(alerts),
        "alerts": alerts,
    }