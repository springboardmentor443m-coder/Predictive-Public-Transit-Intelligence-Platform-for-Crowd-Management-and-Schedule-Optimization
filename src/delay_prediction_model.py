
import os
import sys
import warnings

import joblib
import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import LeaveOneGroupOut
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


# ============================================================
# CONFIGURATION
# ============================================================

INPUT_FILE = os.path.join("models", "historical_delay_target.csv")
MODEL_DIR = "models"
MODEL_FILE = os.path.join(MODEL_DIR, "delay_prediction_model.joblib")

TARGET = "delay_seconds"

# These columns must never be used as model inputs.
# They contain the target itself, information derived from it,
# or timestamps that could introduce leakage.
EXCLUDED_FEATURES = [
    "delay_seconds",
    "arrival_delay_seconds",
    "departure_delay_seconds",
    "collection_time",
    "feed_timestamp",
    "trip_timestamp",
    "trip_id",
]


# ============================================================
# FEATURE ENGINEERING
# ============================================================

def time_to_seconds(value):
    """Convert a GTFS HH:MM:SS time into seconds after midnight.

    GTFS times can exceed 24 hours, so hours are not restricted
    to the usual 0-23 range.
    """
    if pd.isna(value):
        return np.nan

    try:
        parts = str(value).strip().split(":")

        if len(parts) != 3:
            return np.nan

        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = float(parts[2])

        if hours < 0 or not (0 <= minutes < 60):
            return np.nan

        if not (0 <= seconds < 60):
            return np.nan

        return hours * 3600 + minutes * 60 + seconds

    except (ValueError, TypeError):
        return np.nan


def prepare_features(df):
    """Create predictors without using observed delay values."""

    df = df.copy()

    # Convert scheduled times into numerical features.
    if "scheduled_arrival_time" in df.columns:
        df["scheduled_arrival_seconds"] = (
            df["scheduled_arrival_time"].apply(time_to_seconds)
        )

    if "scheduled_departure_time" in df.columns:
        df["scheduled_departure_seconds"] = (
            df["scheduled_departure_time"].apply(time_to_seconds)
        )

    # Keep the original trip IDs separately for group-based evaluation.
    if "trip_id" not in df.columns:
        raise ValueError(
            "The dataset must contain trip_id for trip-based evaluation."
        )

    groups = df["trip_id"].astype(str)

    # Exclude target, delay-derived values, collection timestamps,
    # and trip_id from the predictors.
    drop_columns = [
        column
        for column in EXCLUDED_FEATURES
        if column in df.columns
    ]

    X = df.drop(columns=drop_columns, errors="ignore")

    # Original time strings are redundant after conversion.
    X = X.drop(
        columns=[
            "scheduled_arrival_time",
            "scheduled_departure_time",
        ],
        errors="ignore",
    )

    # Remove columns that contain no usable values.
    X = X.dropna(axis=1, how="all")

    # Ensure numeric-looking columns are numeric.
    for column in X.columns:
        if column in [
            "scheduled_arrival_seconds",
            "scheduled_departure_seconds",
            "stop_sequence",
            "direction_id",
        ]:
            X[column] = pd.to_numeric(X[column], errors="coerce")

    # Treat identifiers and descriptive labels as categories.
    categorical_candidates = [
        "route_id",
        "service_id",
        "direction_id",
        "trip_headsign",
        "shape_id",
        "stop_id",
    ]

    for column in categorical_candidates:
        if column in X.columns:
            X[column] = X[column].astype("string").astype(object)

    # Keep the feature columns aligned with the target rows.
    X = X.reset_index(drop=True)
    groups = groups.reset_index(drop=True)

    return X, groups


# ============================================================
# PIPELINE CREATION
# ============================================================

def create_pipeline(X):

    numeric_features = [
        column
        for column in X.columns
        if pd.api.types.is_numeric_dtype(X[column])
    ]

    categorical_features = [
        column
        for column in X.columns
        if column not in numeric_features
    ]

    transformers = []

    if numeric_features:
        numeric_pipeline = Pipeline(
            steps=[
                (
                    "imputer",
                    SimpleImputer(strategy="median"),
                )
            ]
        )

        transformers.append(
            ("numeric", numeric_pipeline, numeric_features)
        )

    if categorical_features:
        categorical_pipeline = Pipeline(
            steps=[
                (
                    "imputer",
                    SimpleImputer(strategy="most_frequent"),
                ),
                (
                    "encoder",
                    OneHotEncoder(handle_unknown="ignore"),
                ),
            ]
        )

        transformers.append(
            ("categorical", categorical_pipeline, categorical_features)
        )

    if not transformers:
        raise ValueError("No usable predictor features were found.")

    preprocessor = ColumnTransformer(
        transformers=transformers,
        remainder="drop",
    )

    model = RandomForestRegressor(
        n_estimators=200,
        random_state=42,
        n_jobs=-1,
        min_samples_leaf=2,
    )

    return Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("model", model),
        ]
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 65)
    print("V/LINE DELAY PREDICTION MODEL")
    print("=" * 65)

    if not os.path.exists(INPUT_FILE):
        print(f"\nDataset not found: {INPUT_FILE}")
        print("Model status: WAITING FOR REAL DELAY DATA")
        sys.exit(0)

    print("\nLoading historical delay dataset...")
    df = pd.read_csv(INPUT_FILE)

    print(f"Rows loaded: {len(df)}")

    required_columns = [TARGET, "trip_id"]

    missing = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing:
        print(f"\nERROR: Missing required columns: {missing}")
        sys.exit(1)

    df[TARGET] = pd.to_numeric(df[TARGET], errors="coerce")
    df = df.dropna(subset=[TARGET, "trip_id"]).copy()
    df = df[np.isfinite(df[TARGET])].reset_index(drop=True)

    if len(df) < 20:
        print("\nNot enough valid observations to train.")
        print("Collect more genuine realtime observations first.")
        sys.exit(0)

    unique_trips = df["trip_id"].nunique()

    print(f"Valid observations: {len(df)}")
    print(f"Unique trips: {unique_trips}")

    # Negative delays may represent early running.
    # Do not automatically remove them if they are genuine feed values.
    y = df[TARGET].astype(float).reset_index(drop=True)

    X, groups = prepare_features(df)

    print(f"\nPredictor columns ({len(X.columns)}):")
    for column in X.columns:
        print(f"  - {column}")

    forbidden = {
        "delay_seconds",
        "arrival_delay_seconds",
        "departure_delay_seconds",
        "collection_time",
        "feed_timestamp",
        "trip_timestamp",
        "trip_id",
    }

    leakage_columns = forbidden.intersection(X.columns)

    if leakage_columns:
        raise ValueError(
            f"Potential target leakage detected: {sorted(leakage_columns)}"
        )

    print("\nActual delay values are excluded from model inputs.")

    # --------------------------------------------------------
    # Group-based evaluation: hold out one entire trip at a time
    # --------------------------------------------------------

    if unique_trips >= 3:
        print("\nEvaluating with Leave-One-Trip-Out cross-validation...")
        print("Each test fold contains a trip not used for training.")

        logo = LeaveOneGroupOut()

        all_actual = []
        all_predictions = []
        fold_mae = []

        for fold, (train_idx, test_idx) in enumerate(
            logo.split(X, y, groups=groups),
            start=1,
        ):
            X_train = X.iloc[train_idx]
            X_test = X.iloc[test_idx]
            y_train = y.iloc[train_idx]
            y_test = y.iloc[test_idx]

            # A fold needs at least two training rows.
            if len(train_idx) < 2 or len(test_idx) == 0:
                print(f"Fold {fold}: skipped (insufficient rows).")
                continue

            fold_pipeline = create_pipeline(X_train)

            fold_pipeline.fit(X_train, y_train)
            predictions = fold_pipeline.predict(X_test)

            mae = mean_absolute_error(y_test, predictions)
            fold_mae.append(mae)

            all_actual.extend(y_test.tolist())
            all_predictions.extend(predictions.tolist())

            held_out_trip = groups.iloc[test_idx].iloc[0]

            print(
                f"Fold {fold}: held-out trip={held_out_trip}, "
                f"test rows={len(test_idx)}, MAE={mae:.2f} seconds"
            )

        if all_actual:
            overall_mae = mean_absolute_error(
                all_actual, all_predictions
            )
            overall_rmse = mean_squared_error(
                all_actual, all_predictions
            ) ** 0.5

            print("\n" + "=" * 65)
            print("GROUP-BASED EVALUATION")
            print("=" * 65)
            print(f"Out-of-trip MAE : {overall_mae:.2f} seconds")
            print(f"Out-of-trip RMSE: {overall_rmse:.2f} seconds")

            if len(set(all_actual)) >= 2:
                overall_r2 = r2_score(all_actual, all_predictions)
                print(f"Out-of-trip R²  : {overall_r2:.4f}")
            else:
                print("Out-of-trip R²  : undefined (constant test targets)")

            print(
                "\nThese metrics are preliminary. Repeated observations, "
                "few unique trips, and limited target variation restrict "
                "what can be concluded about real-world performance."
            )
        else:
            print("No valid evaluation folds could be completed.")

    else:
        print(
            "\nEvaluation skipped: at least three unique trips are "
            "required for this group-based evaluation."
        )

    # --------------------------------------------------------
    # Train final pipeline on all available observations
    # --------------------------------------------------------

    print("\nTraining final model on all valid observations...")

    final_pipeline = create_pipeline(X)
    final_pipeline.fit(X, y)

    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(final_pipeline, MODEL_FILE)

    print(f"\nSaved final model to: {MODEL_FILE}")
    print(f"Training observations: {len(X)}")
    print(f"Distinct trips: {unique_trips}")
    print("\nModel training completed.")
    print(
        "Note: the saved model is a preliminary prototype, not yet "
        "validated for reliable operational delay forecasting."
    )


if __name__ == "__main__":
    main()
