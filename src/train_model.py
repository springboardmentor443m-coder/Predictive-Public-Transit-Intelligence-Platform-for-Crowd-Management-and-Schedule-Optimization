"""
train_model.py — Train, compare, and persist the best ML regression model.

Models compared:
  1. Linear Regression     — baseline; good for understanding linear patterns
  2. Random Forest         — ensemble of trees; robust, gives feature importance
  3. Gradient Boosting     — sequential boosting; typically best on tabular data

Selection criterion:
  The model with the lowest RMSE on the held-out test set is saved as
  models/best_model.joblib along with a JSON metadata file.

For a viva:
  Q: "Why not use a neural network?"
  A: For structured tabular data of this size (~5,500 rows, 10 features),
     tree-based ensembles consistently outperform or match neural networks
     while being far easier to interpret, train, and debug. Gradient Boosting
     is a well-established choice for tabular regression tasks.

  Q: "How did you prevent overfitting?"
  A: 20% test split (held out before any training); Random Forest and Gradient
     Boosting have internal regularisation (max_depth, n_estimators, learning_rate).
     We report metrics on the unseen test set, not the training set.

Run:
  python src/train_model.py
"""

import sys
import json
import time
import warnings
from pathlib import Path

# Suppress numpy overflow warnings that can appear with LinearRegression
# on Python 3.9 + sklearn 1.x when feature scales are very different.
# This does NOT affect the saved Gradient Boosting model.
warnings.filterwarnings("ignore", category=RuntimeWarning)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import joblib
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

from src.config import (
    FEATURE_COLUMNS,
    ML_RANDOM_SEED,
    MODEL_DIR,
    MODEL_METADATA_PATH,
    MODEL_PATH,
    TARGET_COLUMN,
    TEST_SIZE,
)
from src.data_processing import load_data
from src.feature_engineering import engineer_features, get_feature_matrix


# ──────────────────────────────────────────────────────────────
# Model definitions
# ──────────────────────────────────────────────────────────────
def get_models() -> dict:
    """
    Return a dict of {model_name: unfitted_model_instance}.
    Hyperparameters are reasonable defaults for a dataset of ~5,000 rows.
    """
    return {
        "Linear Regression": Pipeline([
            ("scaler", StandardScaler()),
            ("model",  LinearRegression()),
        ]),
        "Random Forest": RandomForestRegressor(
            n_estimators=200,
            max_depth=12,
            min_samples_leaf=5,
            random_state=ML_RANDOM_SEED,
            n_jobs=-1,
        ),
        "Gradient Boosting": GradientBoostingRegressor(
            n_estimators=300,
            learning_rate=0.08,
            max_depth=5,
            min_samples_leaf=5,
            subsample=0.85,
            random_state=ML_RANDOM_SEED,
        ),
    }


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    """Compute MAE, RMSE, and R² — the three standard regression metrics."""
    mae  = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    r2   = r2_score(y_true, y_pred)
    return {"MAE": round(mae, 3), "RMSE": round(rmse, 3), "R2": round(r2, 4)}


def train_and_evaluate() -> dict:
    """
    Full training pipeline:
      1. Load data
      2. Engineer features
      3. Train/test split
      4. Fit all models
      5. Evaluate on test set
      6. Save best model + metadata

    Returns
    -------
    dict with keys: results, best_model_name, best_metrics, feature_importance
    """
    print("=" * 60)
    print("  Transit Platform — Model Training")
    print("=" * 60)

    # ── 1. Load & engineer ───────────────────────────────────────
    print("\n[1/5] Loading data …")
    df = load_data()
    print(f"      {len(df):,} rows loaded.")

    print("[2/5] Engineering features …")
    df_eng, route_encoder = engineer_features(df)
    X, y = get_feature_matrix(df_eng)
    print(f"      Feature matrix: {X.shape}")

    # ── 2. Train/test split ──────────────────────────────────────
    print("[3/5] Splitting data …")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=ML_RANDOM_SEED
    )
    print(f"      Train: {len(X_train):,}  |  Test: {len(X_test):,}")

    # ── 3. Train & evaluate all models ───────────────────────────
    print("[4/5] Training models …\n")
    models   = get_models()
    results  = {}
    best_name   = None
    best_rmse   = float("inf")
    best_model  = None

    for name, model in models.items():
        t0 = time.time()
        model.fit(X_train, y_train)
        elapsed = time.time() - t0

        y_pred  = model.predict(X_test)
        metrics = compute_metrics(y_test, y_pred)

        results[name] = {**metrics, "train_time_s": round(elapsed, 2)}
        print(f"  {name:<25}  MAE={metrics['MAE']:>6.2f}  "
              f"RMSE={metrics['RMSE']:>6.2f}  R²={metrics['R2']:.4f}  "
              f"({elapsed:.1f}s)")

        if metrics["RMSE"] < best_rmse:
            best_rmse  = metrics["RMSE"]
            best_name  = name
            best_model = model

    print(f"\n  ✅  Best model: {best_name}  (RMSE = {best_rmse:.2f})")

    # ── 4. Feature importance ────────────────────────────────────
    feature_importance = {}
    # Unwrap Pipeline to get the actual estimator
    actual_estimator = (best_model.named_steps["model"]
                        if hasattr(best_model, "named_steps")
                        else best_model)

    if hasattr(actual_estimator, "feature_importances_"):
        importances = actual_estimator.feature_importances_
        feature_importance = dict(zip(FEATURE_COLUMNS, importances.round(4).tolist()))
        print("\n  Feature importance:")
        for feat, imp in sorted(feature_importance.items(), key=lambda x: -x[1]):
            print(f"    {feat:<28} {imp:.4f}")
    elif hasattr(actual_estimator, "coef_"):
        # Linear Regression: use absolute normalised coefficients as proxy
        coefs = np.abs(actual_estimator.coef_)
        coefs_norm = coefs / coefs.sum()
        feature_importance = dict(zip(FEATURE_COLUMNS, coefs_norm.round(4).tolist()))
        print("\n  Normalised coefficient magnitudes (proxy for importance):")
        for feat, imp in sorted(feature_importance.items(), key=lambda x: -x[1]):
            print(f"    {feat:<28} {imp:.4f}")

    # ── 5. Save model and metadata ───────────────────────────────
    print("\n[5/5] Saving model …")
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    # Save model + encoder together as a dict so inference always has both
    joblib.dump(
        {"model": best_model, "route_encoder": route_encoder},
        MODEL_PATH,
    )

    # Best model predictions on test set — saved for the model analytics page
    y_pred_best = best_model.predict(X_test).tolist()

    metadata = {
        "best_model":        best_name,
        "features":          FEATURE_COLUMNS,
        "target":            TARGET_COLUMN,
        "test_size":         TEST_SIZE,
        "train_rows":        len(X_train),
        "test_rows":         len(X_test),
        "metrics":           results,
        "best_metrics":      results[best_name],
        "feature_importance": feature_importance,
        "y_test_sample":     y_test[:200].tolist(),     # subset for chart
        "y_pred_sample":     y_pred_best[:200],
    }

    with open(MODEL_METADATA_PATH, "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"  ✅  Model saved   → {MODEL_PATH}")
    print(f"  ✅  Metadata saved → {MODEL_METADATA_PATH}")
    print("\n" + "=" * 60)

    return {
        "results":          results,
        "best_model_name":  best_name,
        "best_metrics":     results[best_name],
        "feature_importance": feature_importance,
    }


if __name__ == "__main__":
    train_and_evaluate()
