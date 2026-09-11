"""
generate_dataset.py — Generates a realistic synthetic transit dataset.

Run this script once to create data/transit_data.csv.
The dataset is deliberately synthetic (labelled clearly below) so the
project works without any external API or real transit feed.

Design decisions:
- 10 routes, each with different base demand profiles
- Covers ~6 months of hourly observations (~5,000 rows)
- Demand shaped by hour-of-day, day-of-week, weather, and events
- Gaussian noise added so the ML problem is non-trivial but learnable
- 'prev_passenger_count' mimics a simple lag feature (previous-hour demand)

For a viva/demo:
  Q: "Why synthetic data?"
  A: Real GTFS/AVL feeds require API keys and vary by city. Synthetic data
     lets us validate the ML pipeline now; swapping in real data only
     requires replacing this file and re-running train_model.py.
"""

import sys
from pathlib import Path

# Allow running from project root or scripts/ folder
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import pandas as pd
from src.config import DATA_PATH, RANDOM_SEED, ROUTES

# ──────────────────────────────────────────────────────────────
# Route demand profiles
# Each route has (base_demand, peak_morning_multiplier, peak_evening_multiplier)
# These reflect different route characters:
#   Airport Link: higher demand all day, less pronounced peak
#   University Shuttle: strong morning/evening peaks on weekdays only
# ──────────────────────────────────────────────────────────────
ROUTE_PROFILES = {
    "Route 1 - City Centre Express":    {"base": 55, "am_mult": 1.9, "pm_mult": 1.8, "weekend_factor": 0.6},
    "Route 2 - Airport Link":           {"base": 45, "am_mult": 1.4, "pm_mult": 1.3, "weekend_factor": 0.9},
    "Route 3 - University Shuttle":     {"base": 40, "am_mult": 2.2, "pm_mult": 2.0, "weekend_factor": 0.2},
    "Route 4 - North Suburbs":          {"base": 35, "am_mult": 1.7, "pm_mult": 1.6, "weekend_factor": 0.5},
    "Route 5 - South Connector":        {"base": 30, "am_mult": 1.5, "pm_mult": 1.4, "weekend_factor": 0.55},
    "Route 6 - Industrial Park":        {"base": 50, "am_mult": 2.0, "pm_mult": 1.9, "weekend_factor": 0.15},
    "Route 7 - Hospital Line":          {"base": 42, "am_mult": 1.6, "pm_mult": 1.5, "weekend_factor": 0.7},
    "Route 8 - Beach/Leisure":          {"base": 25, "am_mult": 1.1, "pm_mult": 1.8, "weekend_factor": 1.5},
    "Route 9 - East Corridor":          {"base": 38, "am_mult": 1.8, "pm_mult": 1.7, "weekend_factor": 0.5},
    "Route 10 - West Ring":             {"base": 32, "am_mult": 1.6, "pm_mult": 1.5, "weekend_factor": 0.5},
}

# ──────────────────────────────────────────────────────────────
# Hour-of-day demand shape (index 0–23)
# Represents typical urban transit ridership curve
# ──────────────────────────────────────────────────────────────
HOUR_SHAPE = [
    0.05, 0.03, 0.02, 0.02, 0.03, 0.08,   # 00–05: very low / overnight
    0.30, 0.85, 1.00, 0.70, 0.55, 0.60,   # 06–11: morning peak at 08
    0.65, 0.60, 0.55, 0.60, 0.75, 0.95,   # 12–17: midday + building evening
    1.00, 0.80, 0.60, 0.40, 0.20, 0.10,   # 18–23: evening peak at 18
]


def compute_demand(route: str, hour: int, day_of_week: int,
                   is_raining: bool, temperature: float,
                   nearby_event: bool, rng: np.random.Generator) -> float:
    """
    Deterministic demand formula + small Gaussian noise.
    This gives the ML model real patterns to learn.
    """
    profile = ROUTE_PROFILES[route]
    base = profile["base"]

    # Hour shape
    demand = base * HOUR_SHAPE[hour]

    # Peak-hour boost (already encoded in HOUR_SHAPE but amplified per route)
    if 7 <= hour <= 9:
        demand *= profile["am_mult"]
    elif 17 <= hour <= 19:
        demand *= profile["pm_mult"]

    # Weekend effect
    is_weekend = day_of_week >= 5
    if is_weekend:
        demand *= profile["weekend_factor"]

    # Weather effect: rain slightly boosts transit use; cold reduces it
    if is_raining:
        demand *= 1.10
    temp_factor = 1.0 - 0.003 * abs(temperature - 22)   # optimum at 22 °C
    demand *= max(0.7, temp_factor)

    # Nearby event (concerts, sports, etc.) — big crowd spike
    if nearby_event:
        demand *= 1.50

    # Gaussian noise (σ = 10% of demand, min σ = 3)
    noise = rng.normal(0, max(demand * 0.10, 3))
    demand = max(0, demand + noise)

    return round(demand)


def generate_dataset(n_rows: int = 5000) -> pd.DataFrame:
    """
    Generate `n_rows` synthetic transit observations.
    Returns a tidy DataFrame ready for ML training.
    """
    rng = np.random.default_rng(RANDOM_SEED)
    route_names = list(ROUTE_PROFILES.keys())
    records = []

    # Build a pool of (route, hour, day) combos sampled with replacement
    # Bias towards commuting hours so dataset is realistic
    hours  = rng.choice(range(24), size=n_rows,
                        p=[HOUR_SHAPE[h] / sum(HOUR_SHAPE) for h in range(24)])
    days   = rng.integers(0, 7, size=n_rows)       # 0=Mon … 6=Sun
    routes = rng.choice(route_names, size=n_rows)

    # Weather: ~25% chance of rain; temperature normally distributed
    raining = rng.random(size=n_rows) < 0.25
    temps   = rng.normal(loc=20, scale=8, size=n_rows).clip(-5, 42)

    # Events: ~8% of observations have a nearby event
    events  = rng.random(size=n_rows) < 0.08

    prev_counts = []
    for i in range(n_rows):
        # Simulate previous-hour demand (same route, hour-1)
        prev_hour = max(0, hours[i] - 1)
        prev_demand = compute_demand(
            routes[i], prev_hour, days[i],
            bool(raining[i]), float(temps[i]), bool(events[i]), rng
        )
        prev_counts.append(prev_demand)

    passenger_counts = []
    for i in range(n_rows):
        pc = compute_demand(
            routes[i], int(hours[i]), int(days[i]),
            bool(raining[i]), float(temps[i]), bool(events[i]), rng
        )
        passenger_counts.append(pc)

    # Route average demand (will be used as a feature — computed across the whole dataset)
    route_avg = {}
    temp_df = pd.DataFrame({"route": routes, "passenger_count": passenger_counts})
    route_avg = temp_df.groupby("route")["passenger_count"].mean().to_dict()

    df = pd.DataFrame({
        "route":                routes,
        "hour":                 hours.astype(int),
        "day_of_week":          days.astype(int),          # 0=Mon, 6=Sun
        "is_weekend":           (days >= 5).astype(int),
        "temperature":          temps.round(1),
        "is_raining":           raining.astype(int),
        "nearby_event":         events.astype(int),
        "prev_passenger_count": prev_counts,
        "passenger_count":      passenger_counts,
        "vehicle_capacity":     [ROUTES[r] for r in routes],
        "data_source":          "SYNTHETIC",               # Always label synthetic data
    })

    # Add route average demand
    df["route_avg_demand"] = df["route"].map(route_avg).round(1)

    # Derive useful columns
    df["is_peak_hour"] = df["hour"].apply(
        lambda h: 1 if (7 <= h <= 9 or 17 <= h <= 19) else 0
    )
    df["utilisation"] = (df["passenger_count"] / df["vehicle_capacity"]).round(4)

    # Day name for human readability
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    df["day_name"] = df["day_of_week"].apply(lambda d: day_names[d])

    return df


if __name__ == "__main__":
    print("Generating synthetic transit dataset …")
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)

    df = generate_dataset(n_rows=5500)   # ~5,500 rows for a robust ML dataset

    df.to_csv(DATA_PATH, index=False)

    print(f"✅  Dataset saved to: {DATA_PATH}")
    print(f"   Rows      : {len(df):,}")
    print(f"   Columns   : {list(df.columns)}")
    print(f"   Routes    : {df['route'].nunique()}")
    print(f"   Passenger count range: {df['passenger_count'].min()} – {df['passenger_count'].max()}")
    print(f"   Avg utilisation: {df['utilisation'].mean():.2%}")
    print("\nFirst 5 rows:")
    print(df.head().to_string(index=False))
