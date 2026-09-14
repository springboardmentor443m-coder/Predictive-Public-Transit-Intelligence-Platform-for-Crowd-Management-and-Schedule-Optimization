from app.core.config import settings


def congestion_level(total: float) -> str:
    if total >= settings.level_high:
        return "critical"
    if total >= settings.level_medium:
        return "high"
    if total >= settings.level_low:
        return "medium"
    return "low"


def recommend_frequency(predicted_total: float, capacity_per_hour: int = 5000) -> dict:
    """Headway recommendation: more demand -> lower headway (min 2, max 15 min)."""
    load = predicted_total / max(1, capacity_per_hour)
    if load >= 1.0:
        freq = 2
    elif load >= 0.8:
        freq = 3
    elif load >= 0.6:
        freq = 4
    elif load >= 0.4:
        freq = 6
    elif load >= 0.2:
        freq = 8
    else:
        freq = 12
    trains_per_hour = round(60 / freq)
    return {"frequency_min": freq, "trains_per_hour": trains_per_hour,
            "load_factor": round(load, 3),
            "action": "Add trains" if load >= 0.8 else ("Monitor" if load >= 0.4 else "Normal service")}
