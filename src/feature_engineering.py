"""
feature_engineering.py — Transform raw data into ML-ready feature matrices.

Responsibilities:
  1. Encode categorical columns (route → integer label)
  2. Select the exact feature columns the model expects
  3. Provide a single-row feature builder for inference (used by prediction.py)

Why label-encode route instead of one-hot encode?
  - Tree-based models (Random Forest, Gradient Boosting) handle ordinal
    integer encodings well — they don't assume numeric ordering matters.
  - One-hot encoding would add 10 binary columns; unnecessary here.
  - The encoding mapping is saved alongside the model for consistent inference.

For a viva:
  Q: "Why these features?"
  A: route captures route-specific demand patterns; hour + is_peak_hour capture
     time-of-day effects; day_of_week + is_weekend capture weekly patterns;
     temperature + is_raining capture weather demand shifts; nearby_event captures
     event spikes; prev_passenger_count is a lag feature (momentum); route_avg_demand
     is a route-level baseline that helps the model calibrate.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder

from src.config import FEATURE_COLUMNS, TARGET_COLUMN


def build_route_encoder(df: pd.DataFrame) -> LabelEncoder:
    """
    Fit a LabelEncoder on all routes present in the dataset.
    Returns the fitted encoder; must be saved with the model for inference.
    """
    le = LabelEncoder()
    le.fit(df["route"].values)
    return le


def engineer_features(df: pd.DataFrame,
                       route_encoder: LabelEncoder = None
                       ) -> tuple[pd.DataFrame, LabelEncoder]:
    """
    Add engineered columns and return (feature-matrix-ready df, encoder).

    Parameters
    ----------
    df : pd.DataFrame
        Output of data_processing.load_data()
    route_encoder : LabelEncoder, optional
        Pass a pre-fitted encoder for inference (so we don't re-fit on
        the inference row and lose consistency with training encoding).

    Returns
    -------
    df : pd.DataFrame
        DataFrame with 'route_encoded' column added.
    route_encoder : LabelEncoder
        The fitted encoder (either passed in or freshly fitted).
    """
    df = df.copy()

    # ── Route label encoding ─────────────────────────────────────
    if route_encoder is None:
        route_encoder = build_route_encoder(df)

    # Handle unseen routes during inference gracefully
    known_routes = set(route_encoder.classes_)
    df["route_encoded"] = df["route"].apply(
        lambda r: route_encoder.transform([r])[0] if r in known_routes else -1
    )

    # ── Ensure all expected feature columns exist ────────────────
    for col in FEATURE_COLUMNS:
        if col not in df.columns:
            df[col] = 0   # safe default for missing optional columns

    return df, route_encoder


def get_feature_matrix(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """
    Extract X (features) and y (target) arrays from an engineered DataFrame.

    Returns
    -------
    X : np.ndarray  shape (n_samples, n_features)
    y : np.ndarray  shape (n_samples,)
    """
    X = df[FEATURE_COLUMNS].values.astype(float)
    y = df[TARGET_COLUMN].values.astype(float)
    return X, y


def build_inference_row(
    route: str,
    hour: int,
    day_of_week: int,
    temperature: float,
    is_raining: int,
    nearby_event: int,
    prev_passenger_count: float,
    route_avg_demand: float,
    route_encoder: LabelEncoder,
) -> np.ndarray:
    """
    Build a single (1 × n_features) feature array for a one-off prediction.

    This is the function the passenger dashboard calls. It guarantees the
    feature order exactly matches FEATURE_COLUMNS in config.py.

    Parameters
    ----------
    All inputs match what the user enters in the Streamlit passenger form.

    Returns
    -------
    np.ndarray : shape (1, n_features)  — ready to pass to model.predict()
    """
    is_weekend   = 1 if day_of_week >= 5 else 0
    is_peak_hour = 1 if (7 <= hour <= 9 or 17 <= hour <= 19) else 0

    known_routes = set(route_encoder.classes_)
    route_enc    = (route_encoder.transform([route])[0]
                    if route in known_routes else -1)

    # Build in the exact order of FEATURE_COLUMNS
    row = [
        route_enc,
        hour,
        day_of_week,
        is_weekend,
        is_peak_hour,
        temperature,
        is_raining,
        nearby_event,
        prev_passenger_count,
        route_avg_demand,
    ]
    return np.array(row, dtype=float).reshape(1, -1)


if __name__ == "__main__":
    from src.data_processing import load_data

    print("Testing feature_engineering.py …")
    df = load_data()
    df_eng, encoder = engineer_features(df)

    X, y = get_feature_matrix(df_eng)
    print(f"Feature matrix shape : {X.shape}")
    print(f"Target shape         : {y.shape}")
    print(f"Features             : {FEATURE_COLUMNS}")
    print(f"Route classes        : {list(encoder.classes_)}")
    print(f"X sample (first row) : {X[0]}")
    print(f"y sample (first 5)   : {y[:5]}")
