def generate_recommendations(
    predicted_ridership,
    traffic_level,
    delay_minutes
):
    recommendations = []

    if predicted_ridership >= 500:
        recommendations.append(
            "Increase train frequency during high-demand periods."
        )
    elif predicted_ridership <= 100:
        recommendations.append(
            "Consider reducing train frequency during low-demand periods."
        )

    if traffic_level == "high":
        recommendations.append(
            "Monitor high-traffic routes and consider additional service."
        )

    if delay_minutes > 15:
        recommendations.append(
            "Activate major delay response and notify operators."
        )
    elif delay_minutes > 5:
        recommendations.append(
            "Monitor the delay and consider frequency adjustment."
        )

    if not recommendations:
        recommendations.append(
            "Current conditions are within normal operating levels."
        )

    return {
        "predicted_ridership": predicted_ridership,
        "traffic_level": traffic_level,
        "delay_minutes": delay_minutes,
        "recommendations": recommendations
    }
