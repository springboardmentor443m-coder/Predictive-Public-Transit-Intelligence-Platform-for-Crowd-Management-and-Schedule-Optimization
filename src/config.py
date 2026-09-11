"""
config.py — Central configuration for the Transit Intelligence Platform.

All thresholds, capacities, file paths, and model settings are defined here.
Import this module in any other module instead of hardcoding values.

Why a config file?
- Changing a threshold (e.g. what counts as "High" crowding) only needs
  one edit here — every part of the app picks it up automatically.
- Easy to demo: you can live-edit thresholds and restart the app.
"""

from pathlib import Path

# ─────────────────────────────────────────────
# Project root — everything is relative to this
# ─────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# ─────────────────────────────────────────────
# File paths
# ─────────────────────────────────────────────
DATA_PATH = PROJECT_ROOT / "data" / "transit_data.csv"
MODEL_DIR = PROJECT_ROOT / "models"
MODEL_PATH = MODEL_DIR / "best_model.joblib"
MODEL_METADATA_PATH = MODEL_DIR / "model_metadata.json"

# ─────────────────────────────────────────────
# Dataset generation settings
# ─────────────────────────────────────────────
RANDOM_SEED = 42          # For reproducibility

# Route definitions: name → default vehicle capacity (passengers)
ROUTES = {
    "Route 1 - City Centre Express":       100,
    "Route 2 - Airport Link":              100,
    "Route 3 - University Shuttle":        100,
    "Route 4 - North Suburbs":             100,
    "Route 5 - South Connector":           100,
    "Route 6 - Industrial Park":           100,
    "Route 7 - Hospital Line":             100,
    "Route 8 - Beach/Leisure":             100,
    "Route 9 - East Corridor":             100,
    "Route 10 - West Ring":                100,
}

# Default capacity used when route is not in the dict above
DEFAULT_VEHICLE_CAPACITY = 100

# ─────────────────────────────────────────────
# Crowd-level thresholds  (utilisation = passengers / capacity)
# ─────────────────────────────────────────────
# Change these values to adjust what counts as each crowd level.
CROWD_THRESHOLDS = {
    "Low":      (0.00, 0.50),   # 0 – 49 % utilisation
    "Moderate": (0.50, 0.75),   # 50 – 74 %
    "High":     (0.75, 0.90),   # 75 – 89 %
    "Critical": (0.90, 1.00),   # 90 %+
}

# Colours used in Streamlit / Plotly for each crowd level
CROWD_COLOURS = {
    "Low":      "#2ecc71",   # green
    "Moderate": "#f39c12",   # amber
    "High":     "#e67e22",   # orange
    "Critical": "#e74c3c",   # red
}

# ─────────────────────────────────────────────
# Schedule optimiser recommendation rules
# ─────────────────────────────────────────────
RECOMMENDATION_RULES = {
    "Critical": "Add an extra vehicle / service run immediately.",
    "High":     "Increase service frequency (reduce headway).",
    "Moderate": "Current service level is adequate — monitor closely.",
    "Low":      "Consider reviewing frequency; consolidation may save costs.",
}

# Utilisation below this → flag as Very Low demand
VERY_LOW_DEMAND_THRESHOLD = 0.20

# ─────────────────────────────────────────────
# Machine-learning settings
# ─────────────────────────────────────────────
TEST_SIZE       = 0.20   # Fraction of data held out for evaluation
ML_RANDOM_SEED  = 42

# Features fed into every model  (must match columns produced by feature_engineering.py)
FEATURE_COLUMNS = [
    "route_encoded",
    "hour",
    "day_of_week",
    "is_weekend",
    "is_peak_hour",
    "temperature",
    "is_raining",
    "nearby_event",
    "prev_passenger_count",
    "route_avg_demand",
]

TARGET_COLUMN = "passenger_count"
