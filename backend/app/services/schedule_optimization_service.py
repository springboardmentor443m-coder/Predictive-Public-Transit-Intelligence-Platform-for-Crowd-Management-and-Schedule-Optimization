def optimize_schedule(avg_ridership, current_frequency=10):
    if avg_ridership >= 500:
        demand_level = "peak"
        recommended_frequency = max(2, current_frequency - 3)
        action = "Increase train frequency"
    elif avg_ridership <= 100:
        demand_level = "low"
        recommended_frequency = current_frequency + 3
        action = "Reduce train frequency"
    else:
        demand_level = "normal"
        recommended_frequency = current_frequency
        action = "Maintain current frequency"

    return {
        "demand_level": demand_level,
        "current_frequency_minutes": current_frequency,
        "recommended_frequency_minutes": recommended_frequency,
        "action": action
    }
