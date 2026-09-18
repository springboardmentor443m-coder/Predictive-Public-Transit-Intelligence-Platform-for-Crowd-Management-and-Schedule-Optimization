"""
AI MetroFlow - Core Utilities Module
Provides data loading, schema validation, feature encoding, metrics evaluation,
visualization, and model serialization functions for subway crowd prediction.
"""

import os
import logging
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime

import joblib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for headless plotting
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report,
)

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("MetroFlow.Utils")

# Default potential data paths
POTENTIAL_DATA_PATHS = [
    os.path.join("data", "features.csv"),
    os.path.abspath(r"C:\Users\WaterMelon\OneDrive\Desktop\SpringBoard\MetroFlow\data\features.csv"),
    os.path.join("..", "MetroFlow", "data", "features.csv"),
]

DEFAULT_MODEL_PATH = os.path.join("models", "congestion_model.pkl")
DEFAULT_COMPAT_PATH = os.path.join("models", "model.pkl")
FIGURES_DIR = os.path.join("reports", "figures")


def get_data_path(custom_path: Optional[str] = None) -> str:
    """Resolve and return an existing path to features.csv."""
    if custom_path and os.path.exists(custom_path):
        return custom_path
    for p in POTENTIAL_DATA_PATHS:
        if os.path.exists(p):
            return p
    raise FileNotFoundError(
        f"features.csv not found in any standard location: {POTENTIAL_DATA_PATHS}"
    )


def load_and_validate_data(
    filepath: Optional[str] = None,
    sample_size: Optional[int] = 150000,
    random_state: int = 42,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Loads dataset, performs data validation checks, and returns a summary.
    
    Args:
        filepath: Path to CSV dataset (auto-resolved if None).
        sample_size: Number of records to sample for training efficiency (None for full data).
        random_state: Random seed for reproducible sampling.
        
    Returns:
        df: Loaded pandas DataFrame.
        summary: Dictionary containing validation statistics.
    """
    resolved_path = get_data_path(filepath)
    logger.info("Loading dataset from: %s", resolved_path)
    
    if sample_size is not None:
        logger.info("Sampling %d rows for balanced, high-efficiency training...", sample_size)
        df = pd.read_csv(resolved_path, nrows=sample_size)
    else:
        logger.info("Loading full dataset (may require high memory)...")
        df = pd.read_csv(resolved_path)
    
    missing_counts = df.isnull().sum().to_dict()
    total_missing = sum(missing_counts.values())
    
    if "Congestion_Level" not in df.columns:
        raise ValueError("Target column 'Congestion_Level' missing from dataset.")
    
    class_counts = df["Congestion_Level"].value_counts().to_dict()
    class_props = df["Congestion_Level"].value_counts(normalize=True).to_dict()
    
    summary = {
        "filepath": resolved_path,
        "rows": len(df),
        "columns": len(df.columns),
        "column_names": list(df.columns),
        "total_missing_values": int(total_missing),
        "missing_per_column": {k: int(v) for k, v in missing_counts.items() if v > 0},
        "class_counts": class_counts,
        "class_proportions": {k: round(float(v), 4) for k, v in class_props.items()},
    }
    
    logger.info("Data loaded successfully. Rows: %d, Columns: %d", summary["rows"], summary["columns"])
    logger.info("Class distribution: %s", summary["class_counts"])
    if total_missing > 0:
        logger.warning("Missing values detected: %s", summary["missing_per_column"])
    else:
        logger.info("Data Validation Passed: 0 missing values detected.")
        
    return df, summary


def get_feature_definitions() -> Dict[str, List[str]]:
    """Defines feature sets for leakage comparison and production modeling."""
    base_temporal = [
        "hour",
        "day",
        "month",
        "year",
        "day_of_week",
        "is_weekend",
        "is_peak_hour",
    ]
    base_spatial = [
        "Latitude",
        "Longitude",
    ]
    categorical_cols = [
        "Borough",
        "Structure",
        "Stop Name",
    ]
    leakage_cols = [
        "Entries",
        "Exits",
    ]
    
    return {
        "temporal": base_temporal,
        "spatial": base_spatial,
        "categorical": categorical_cols,
        "leakage": leakage_cols,
        "encoded_categorical": [f"{col}_encoded" for col in categorical_cols],
    }


def preprocess_features(
    df: pd.DataFrame,
    is_training: bool = True,
    encoders: Optional[Dict[str, LabelEncoder]] = None,
    include_leakage_features: bool = False,
) -> Tuple[pd.DataFrame, Dict[str, LabelEncoder], List[str]]:
    """
    Encodes categorical features and builds the feature matrix.
    
    Args:
        df: Input DataFrame.
        is_training: Whether fitting encoders or transforming during inference.
        encoders: Pre-fitted encoders dictionary if is_training=False.
        include_leakage_features: Whether to include Entries and Exits for comparison.
        
    Returns:
        X: Processed feature DataFrame.
        encoders: Dictionary of fitted LabelEncoders.
        feature_cols: List of final feature column names.
    """
    df_proc = df.copy()
    feat_defs = get_feature_definitions()
    
    if encoders is None:
        encoders = {}
    
    # Process categorical variables with robust unseen-label handling
    for col in feat_defs["categorical"]:
        encoded_col = f"{col}_encoded"
        if col in df_proc.columns:
            str_series = df_proc[col].astype(str).fillna("Unknown")
            if is_training:
                le = LabelEncoder()
                df_proc[encoded_col] = le.fit_transform(str_series)
                encoders[col] = le
            else:
                le = encoders[col]
                # Map unseen categories to a known class safely
                known_classes = set(le.classes_)
                safe_series = str_series.map(lambda x: x if x in known_classes else le.classes_[0])
                df_proc[encoded_col] = le.transform(safe_series)
        else:
            # Fallback if categorical column not supplied
            df_proc[encoded_col] = 0
            
    # Assemble feature columns list
    feature_cols = (
        feat_defs["temporal"]
        + feat_defs["spatial"]
        + [f"{col}_encoded" for col in feat_defs["categorical"]]
    )
    
    if include_leakage_features:
        feature_cols = feature_cols + feat_defs["leakage"]
        
    # Ensure all required features are present
    missing_feats = [col for col in feature_cols if col not in df_proc.columns]
    if missing_feats:
        raise KeyError(f"Missing required feature columns in input: {missing_feats}")
        
    X = df_proc[feature_cols].copy()
    # Fill any numerical NaNs with median/0
    X = X.fillna(0)
    
    return X, encoders, feature_cols


def evaluate_model(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    model_name: str = "Model",
) -> Dict[str, Any]:
    """
    Calculates Accuracy, Precision, Recall, F1 (weighted and macro),
    and Confusion Matrix.
    """
    acc = accuracy_score(y_true, y_pred)
    prec_w = precision_score(y_true, y_pred, average="weighted", zero_division=0)
    rec_w = recall_score(y_true, y_pred, average="weighted", zero_division=0)
    f1_w = f1_score(y_true, y_pred, average="weighted", zero_division=0)
    
    prec_m = precision_score(y_true, y_pred, average="macro", zero_division=0)
    rec_m = recall_score(y_true, y_pred, average="macro", zero_division=0)
    f1_m = f1_score(y_true, y_pred, average="macro", zero_division=0)
    
    cm = confusion_matrix(y_true, y_pred, labels=["Low", "Medium", "High"])
    clf_report = classification_report(y_true, y_pred, digits=4, zero_division=0)
    
    metrics = {
        "model_name": model_name,
        "accuracy": round(float(acc), 4),
        "precision_weighted": round(float(prec_w), 4),
        "recall_weighted": round(float(rec_w), 4),
        "f1_weighted": round(float(f1_w), 4),
        "precision_macro": round(float(prec_m), 4),
        "recall_macro": round(float(rec_m), 4),
        "f1_macro": round(float(f1_m), 4),
        "confusion_matrix": cm.tolist(),
        "classification_report": clf_report,
    }
    
    logger.info(
        "[%s] Accuracy: %.4f | F1 (Weighted): %.4f | Precision: %.4f | Recall: %.4f",
        model_name,
        metrics["accuracy"],
        metrics["f1_weighted"],
        metrics["precision_weighted"],
        metrics["recall_weighted"],
    )
    return metrics


def plot_confusion_matrix(
    cm: np.ndarray,
    classes: List[str],
    title: str,
    output_path: str,
) -> None:
    """Plots and saves a styled Confusion Matrix heatmap."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.figure(figsize=(6, 5))
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=classes,
        yticklabels=classes,
        cbar=True,
    )
    plt.title(title, fontsize=12, fontweight="bold", pad=12)
    plt.xlabel("Predicted Congestion Level", fontsize=10)
    plt.ylabel("Actual Congestion Level", fontsize=10)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    logger.info("Saved confusion matrix plot: %s", output_path)


def plot_feature_importances(
    importances: Dict[str, float],
    title: str,
    output_path: str,
    top_n: int = 12,
) -> None:
    """Plots and saves a styled horizontal bar chart of feature importances."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    sorted_items = sorted(importances.items(), key=lambda x: x[1], reverse=True)[:top_n]
    features = [x[0] for x in sorted_items][::-1]
    scores = [x[1] for x in sorted_items][::-1]
    
    plt.figure(figsize=(8, 5))
    bars = plt.barh(features, scores, color="#1f77b4", edgecolor="#0e466d")
    plt.xlabel("Relative Importance Score", fontsize=10)
    plt.title(title, fontsize=12, fontweight="bold", pad=12)
    plt.xlim(0, max(scores) * 1.15)
    
    for bar in bars:
        width = bar.get_width()
        plt.text(
            width + 0.003,
            bar.get_y() + bar.get_height() / 2,
            f"{width:.4f}",
            va="center",
            fontsize=9,
        )
        
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    logger.info("Saved feature importance plot: %s", output_path)


def get_congestion_recommendation(congestion_level: str, confidence: Optional[float] = None) -> str:
    """
    Returns an actionable, human-readable transit scheduling and crowd management recommendation.
    """
    level_normalized = congestion_level.strip().capitalize()
    
    if level_normalized == "High":
        return (
            "High congestion predicted. Consider increasing train frequency, "
            "dispatching standby trains, and deploying platform crowd control personnel."
        )
    elif level_normalized == "Medium":
        return (
            "Moderate congestion predicted. Maintain standard scheduled frequency; "
            "monitor passenger inflows at turnstiles and connecting line transfers."
        )
    elif level_normalized == "Low":
        return (
            "Low congestion predicted. Standard or reduced train frequency is sufficient; "
            "optimal time window for maintenance operations and energy-saving schedules."
        )
    else:
        return "Unknown congestion tier. Monitor station real-time telemetry."


def save_model_bundle(bundle: Dict[str, Any], filepath: str = DEFAULT_MODEL_PATH) -> None:
    """Saves the complete model bundle with metadata to disk."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    bundle["saved_at"] = datetime.utcnow().isoformat()
    joblib.dump(bundle, filepath)
    logger.info("Model bundle successfully saved to %s", filepath)
    
    # Save copy to compatibility path if different
    if filepath != DEFAULT_COMPAT_PATH:
        joblib.dump(bundle, DEFAULT_COMPAT_PATH)
        logger.info("Compatibility copy saved to %s", DEFAULT_COMPAT_PATH)


def load_model_bundle(filepath: str = DEFAULT_MODEL_PATH) -> Dict[str, Any]:
    """Loads model bundle from disk."""
    if not os.path.exists(filepath):
        if os.path.exists(DEFAULT_COMPAT_PATH):
            filepath = DEFAULT_COMPAT_PATH
        else:
            raise FileNotFoundError(f"Model artifact not found at {filepath}")
    bundle = joblib.load(filepath)
    logger.info("Loaded model bundle from %s (Algorithm: %s)", filepath, bundle.get("model_name", "Unknown"))
    return bundle
