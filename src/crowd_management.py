"""
crowd_management.py — Utilisation calculation and crowd-level classification.

Key concepts:
  utilisation = passenger_count / vehicle_capacity

  Crowd levels are defined in config.CROWD_THRESHOLDS.
  Thresholds are deliberately configurable — a demo can change what counts
  as "Critical" without touching any other file.

For a viva:
  Q: "How do you define 'overcrowded'?"
  A: We use utilisation ratio, not absolute numbers, so the system works
     for routes with different vehicle sizes. A bus with 80 seats at 90%
     full (72 passengers) is just as critical as a larger coach at 90%.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd

from src.config import (
    CROWD_COLOURS,
    CROWD_THRESHOLDS,
    DEFAULT_VEHICLE_CAPACITY,
    ROUTES,
    VERY_LOW_DEMAND_THRESHOLD,
)


def classify_crowd(utilisation: float) -> str:
    """
    Map a utilisation ratio (0.0–1.0+) to a crowd-level label.

    Parameters
    ----------
    utilisation : float
        passenger_count / vehicle_capacity

    Returns
    -------
    str : one of "Low", "Moderate", "High", "Critical"
    """
    # Critical is anything above the High upper bound
    if utilisation >= CROWD_THRESHOLDS["Critical"][0]:
        return "Critical"
    elif utilisation >= CROWD_THRESHOLDS["High"][0]:
        return "High"
    elif utilisation >= CROWD_THRESHOLDS["Moderate"][0]:
        return "Moderate"
    else:
        return "Low"


def get_crowd_colour(level: str) -> str:
    """Return the hex colour string for a given crowd level (for Streamlit UI)."""
    return CROWD_COLOURS.get(level, "#95a5a6")


def compute_utilisation(passenger_count: float, route: str = None,
                        capacity: int = None) -> float:
    """
    Compute utilisation ratio.

    Priority: explicit capacity > route lookup > default.
    """
    if capacity is None or capacity <= 0:
        capacity = ROUTES.get(route, DEFAULT_VEHICLE_CAPACITY) if route else DEFAULT_VEHICLE_CAPACITY
    return round(passenger_count / max(capacity, 1), 4)


def classify_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add 'utilisation' and 'crowd_level' columns to a dataframe.

    Expects 'passenger_count' and 'vehicle_capacity' (or 'route') columns.

    Returns
    -------
    pd.DataFrame : copy of df with two new columns
    """
    df = df.copy()

    if "utilisation" not in df.columns:
        df["utilisation"] = df.apply(
            lambda r: compute_utilisation(
                r["passenger_count"],
                route=r.get("route"),
                capacity=r.get("vehicle_capacity"),
            ),
            axis=1,
        )

    df["crowd_level"] = df["utilisation"].apply(classify_crowd)
    return df


def get_crowd_summary(df: pd.DataFrame) -> dict:
    """
    Return percentage breakdown of each crowd level in a dataset.
    Useful for the operator dashboard distribution chart.
    """
    if "crowd_level" not in df.columns:
        df = classify_dataframe(df)

    total = len(df)
    summary = {}
    for level in ["Low", "Moderate", "High", "Critical"]:
        count = (df["crowd_level"] == level).sum()
        summary[level] = {
            "count":   int(count),
            "percent": round(count / total * 100, 1) if total > 0 else 0.0,
            "colour":  CROWD_COLOURS[level],
        }
    return summary


def flag_high_risk_slots(df: pd.DataFrame,
                          levels: list = None) -> pd.DataFrame:
    """
    Filter a dataframe to only rows with High or Critical crowd levels.
    Useful for the operator's "alerts" section.
    """
    if levels is None:
        levels = ["High", "Critical"]

    if "crowd_level" not in df.columns:
        df = classify_dataframe(df)

    return df[df["crowd_level"].isin(levels)].copy()


def is_very_low_demand(utilisation: float) -> bool:
    """Return True if utilisation is below the very-low threshold."""
    return utilisation < VERY_LOW_DEMAND_THRESHOLD


if __name__ == "__main__":
    print("Testing crowd_management.py …\n")
    test_cases = [
        (0.10, "Route 1 - City Centre Express"),
        (0.55, "Route 2 - Airport Link"),
        (0.82, "Route 3 - University Shuttle"),
        (0.95, "Route 6 - Industrial Park"),
        (1.10, "Route 8 - Beach/Leisure"),   # over-capacity edge case
    ]
    print(f"{'Utilisation':>14}  {'Level':>10}  {'Colour':>9}")
    print("-" * 40)
    for util, route in test_cases:
        level  = classify_crowd(util)
        colour = get_crowd_colour(level)
        print(f"{util:>14.2f}  {level:>10}  {colour:>9}")

    print("\nCrowd summary from small test data:")
    import pandas as pd
    test_df = pd.DataFrame({
        "passenger_count": [5, 50, 80, 95, 110],
        "vehicle_capacity": [100, 100, 100, 100, 100],
    })
    print(get_crowd_summary(test_df))
