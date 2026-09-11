"""
schedule_optimizer.py — Rule-based schedule recommendation engine.

Design philosophy:
  Every recommendation must:
    1. Have a clear crowd level that triggered it.
    2. State what action to take.
    3. Explain WHY (shown in the UI for transparency).

  This is intentionally NOT a mathematical optimiser. True schedule
  optimisation (e.g. mixed-integer programming) is complex and fragile.
  A transparent rule-based engine is more useful for demonstration and
  easier to understand, audit, and modify.

For a viva:
  Q: "Why not use linear programming for schedule optimisation?"
  A: LP optimisation requires precise cost functions, feasibility constraints,
     and detailed timetable data — none of which we have in a synthetic dataset.
     A rule-based engine is easier to understand, gives transparent reasoning,
     and is common in real transit management systems as a first-pass tool.

  Q: "What would you add in a real system?"
  A: Real systems add constraints: driver shift limits, depot constraints,
     vehicle fleet size, and costs. Then LP or metaheuristics (e.g. genetic
     algorithms) become appropriate.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import (
    RECOMMENDATION_RULES,
    VERY_LOW_DEMAND_THRESHOLD,
    CROWD_THRESHOLDS,
)
from src.crowd_management import classify_crowd, compute_utilisation


def generate_recommendation(
    route: str,
    hour: int,
    passenger_count: float,
    capacity: int,
) -> dict:
    """
    Generate a single recommendation for one route/hour slot.

    Parameters
    ----------
    route           : Route name
    hour            : Hour of day (0–23)
    passenger_count : Predicted or actual passenger count
    capacity        : Vehicle capacity

    Returns
    -------
    dict with keys:
      route, hour, passenger_count, capacity, utilisation,
      crowd_level, action, reason, priority (1=highest)
    """
    utilisation = compute_utilisation(passenger_count, capacity=capacity)
    crowd_level = classify_crowd(utilisation)

    # Base action from the rule table
    action = RECOMMENDATION_RULES[crowd_level]

    # Build a human-readable reason
    pct = round(utilisation * 100, 1)
    hour_str = f"{hour:02d}:00"

    reasons = {
        "Critical": (
            f"Predicted {int(passenger_count)} passengers on {route} at {hour_str} "
            f"fills {pct}% of capacity ({capacity} seats). "
            "This is critically overcrowded. An extra service run will "
            "immediately reduce wait times and passenger discomfort."
        ),
        "High": (
            f"Predicted {int(passenger_count)} passengers on {route} at {hour_str} "
            f"fills {pct}% of capacity. "
            "Increasing service frequency (shorter headway) will distribute "
            "demand and prevent the situation becoming critical."
        ),
        "Moderate": (
            f"Predicted {int(passenger_count)} passengers on {route} at {hour_str} "
            f"fills {pct}% of capacity. "
            "Current service level is adequate. Continue monitoring."
        ),
        "Low": (
            f"Predicted {int(passenger_count)} passengers on {route} at {hour_str} "
            f"fills only {pct}% of capacity. "
        ),
    }

    # Add very-low-demand note
    reason = reasons[crowd_level]
    if crowd_level == "Low":
        if utilisation < VERY_LOW_DEMAND_THRESHOLD:
            reason += (
                "Demand is very low. Consider consolidating with another "
                "service or reducing frequency to save operational costs."
            )
        else:
            reason += "No action required at this time."

    # Priority: Critical=1, High=2, Moderate=3, Low=4
    priority_map = {"Critical": 1, "High": 2, "Moderate": 3, "Low": 4}

    return {
        "route":           route,
        "hour":            hour,
        "hour_str":        f"{hour:02d}:00",
        "passenger_count": round(passenger_count, 1),
        "capacity":        capacity,
        "utilisation":     round(utilisation * 100, 1),   # percent
        "crowd_level":     crowd_level,
        "action":          action,
        "reason":          reason,
        "priority":        priority_map[crowd_level],
    }


def generate_daily_recommendations(
    route: str,
    hourly_profile: list[dict],
    capacity: int,
) -> list[dict]:
    """
    Generate recommendations for all 24 hours of a route's predicted daily profile.

    Parameters
    ----------
    route          : Route name
    hourly_profile : Output of prediction.predict_hourly_profile()
                     (list of {"hour": h, "predicted_count": c, "utilisation": u})
    capacity       : Vehicle capacity for this route

    Returns
    -------
    list of recommendation dicts, sorted by priority then hour
    """
    recs = []
    for slot in hourly_profile:
        rec = generate_recommendation(
            route=route,
            hour=slot["hour"],
            passenger_count=slot["predicted_count"],
            capacity=capacity,
        )
        recs.append(rec)

    # Sort: most urgent first, then by hour
    recs.sort(key=lambda r: (r["priority"], r["hour"]))
    return recs


def get_priority_recommendations(
    route: str,
    hourly_profile: list[dict],
    capacity: int,
    levels: list = None,
) -> list[dict]:
    """
    Return only High / Critical recommendations — the operator's action list.
    """
    if levels is None:
        levels = ["High", "Critical"]

    all_recs = generate_daily_recommendations(route, hourly_profile, capacity)
    return [r for r in all_recs if r["crowd_level"] in levels]


if __name__ == "__main__":
    print("Testing schedule_optimizer.py …\n")

    # Simulate a small hourly profile
    test_profile = [
        {"hour": 7,  "predicted_count": 92,  "utilisation": 0.92},
        {"hour": 8,  "predicted_count": 105, "utilisation": 1.05},
        {"hour": 12, "predicted_count": 55,  "utilisation": 0.55},
        {"hour": 17, "predicted_count": 80,  "utilisation": 0.80},
        {"hour": 22, "predicted_count": 12,  "utilisation": 0.12},
    ]

    recs = generate_daily_recommendations(
        route="Route 1 - City Centre Express",
        hourly_profile=test_profile,
        capacity=100,
    )

    for r in recs:
        print(f"  [{r['crowd_level']:>8}] {r['hour_str']}  "
              f"{r['utilisation']:>5.1f}%  →  {r['action']}")
        print(f"           {r['reason'][:80]}…")
        print()
