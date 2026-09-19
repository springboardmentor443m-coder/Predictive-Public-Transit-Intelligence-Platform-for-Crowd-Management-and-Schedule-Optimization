def handle_delay(delay_minutes, scheduled_frequency=10):
    if delay_minutes <= 5:
        severity = "minor"
        action = "Monitor delay"
    elif delay_minutes <= 15:
        severity = "moderate"
        action = "Adjust train frequency"
    else:
        severity = "major"
        action = "Activate delay response and notify operators"

    return {
        "delay_minutes": delay_minutes,
        "severity": severity,
        "scheduled_frequency_minutes": scheduled_frequency,
        "recommended_action": action
    }
