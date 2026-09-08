def recommend_frequency(density: float, label: str) -> str:
    """
    Placeholder recommendation engine (to be fully wired up with dynamic
    headway optimization and downstream delay propagation in Phase 3/4).
    """
    if label == "critical":
        return "Increase frequency by 4 trains/hour (reduce headway by 3 min)"
    elif label == "high":
        return "Increase frequency by 2 trains/hour (reduce headway by 1.5 min)"
    elif label == "medium":
        return "Maintain current schedule; stand by reserve trains at yard"
    else:
        return "Maintain standard off-peak frequency"
