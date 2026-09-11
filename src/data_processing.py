"""
data_processing.py — Load, validate, and clean the transit CSV dataset.

This module is the single entry point for raw data. All other modules
call load_data() instead of reading the CSV directly.

Why separate this from feature engineering?
- Keeps concerns separate: loading/validation vs. transformation.
- If we swap to a real API later, only this file changes.
- Easy to unit test loading independently of feature building.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import numpy as np
from src.config import DATA_PATH, ROUTES, DEFAULT_VEHICLE_CAPACITY


# Columns that must be present in the CSV for the app to work
REQUIRED_COLUMNS = [
    "route", "hour", "day_of_week", "is_weekend",
    "temperature", "is_raining", "nearby_event",
    "prev_passenger_count", "passenger_count", "vehicle_capacity",
]


def load_data(path: Path = DATA_PATH) -> pd.DataFrame:
    """
    Load and validate the transit CSV dataset.

    Returns
    -------
    pd.DataFrame
        Cleaned dataframe ready for feature engineering.

    Raises
    ------
    FileNotFoundError
        If the CSV does not exist. Callers (UI pages) should catch this
        and show a user-friendly message.
    ValueError
        If required columns are missing or data is malformed.
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(
            f"Dataset not found at {path}.\n"
            "Run: python scripts/generate_dataset.py"
        )

    df = pd.read_csv(path)

    # ── Column validation ────────────────────────────────────────
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Dataset is missing required columns: {missing}")

    # ── Type coercion ────────────────────────────────────────────
    int_cols = ["hour", "day_of_week", "is_weekend", "is_raining",
                "nearby_event", "prev_passenger_count",
                "passenger_count", "vehicle_capacity"]
    for col in int_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    df["temperature"] = pd.to_numeric(df["temperature"], errors="coerce").fillna(20.0)
    df["route"] = df["route"].astype(str).str.strip()

    # ── Range validation ─────────────────────────────────────────
    # Clip hour to valid range (handles any corrupt rows)
    df["hour"] = df["hour"].clip(0, 23)
    df["day_of_week"] = df["day_of_week"].clip(0, 6)
    df["passenger_count"] = df["passenger_count"].clip(0, None)   # no negatives

    # ── Fill vehicle_capacity for any routes not in config ───────
    df["vehicle_capacity"] = df.apply(
        lambda row: ROUTES.get(row["route"], DEFAULT_VEHICLE_CAPACITY)
        if row["vehicle_capacity"] <= 0 else row["vehicle_capacity"],
        axis=1,
    )

    # ── Derived columns (cheap, always useful) ───────────────────
    if "is_peak_hour" not in df.columns:
        df["is_peak_hour"] = df["hour"].apply(
            lambda h: 1 if (7 <= h <= 9 or 17 <= h <= 19) else 0
        )

    if "route_avg_demand" not in df.columns:
        route_avg = df.groupby("route")["passenger_count"].transform("mean")
        df["route_avg_demand"] = route_avg.round(1)

    if "utilisation" not in df.columns:
        df["utilisation"] = (df["passenger_count"] / df["vehicle_capacity"]).round(4)

    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday",
                 "Friday", "Saturday", "Sunday"]
    if "day_name" not in df.columns:
        df["day_name"] = df["day_of_week"].apply(lambda d: day_names[d])

    return df


def get_data_summary(df: pd.DataFrame) -> dict:
    """
    Return a summary dict useful for the operator dashboard KPI cards.
    """
    return {
        "total_routes":      df["route"].nunique(),
        "total_records":     len(df),
        "avg_demand":        round(df["passenger_count"].mean(), 1),
        "peak_demand":       int(df["passenger_count"].max()),
        "avg_utilisation":   round(df["utilisation"].mean() * 100, 1),
        "pct_high_critical": round(
            (df["utilisation"] >= 0.75).mean() * 100, 1
        ),
    }


def get_route_list(df: pd.DataFrame) -> list[str]:
    """Return sorted list of unique route names."""
    return sorted(df["route"].unique().tolist())


if __name__ == "__main__":
    print("Testing data_processing.py …")
    df = load_data()
    print(f"Loaded {len(df):,} rows × {len(df.columns)} columns")
    print(f"Routes : {get_route_list(df)}")
    print(f"Summary: {get_data_summary(df)}")
    print("\nDtypes:")
    print(df.dtypes)
    print("\nNull counts:")
    print(df.isnull().sum())
