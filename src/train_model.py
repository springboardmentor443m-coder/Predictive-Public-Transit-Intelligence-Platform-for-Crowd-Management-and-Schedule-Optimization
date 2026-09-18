"""
AI MetroFlow - Machine Learning Model Training & Evaluation Pipeline
Trains and compares Decision Tree, Random Forest, and XGBoost classifiers
to predict subway Congestion_Level (Low, Medium, High).
Performs target leakage analysis and automatically persists the best model.
"""

import os
import sys
import time
import argparse
import logging
from typing import Dict, Any, List, Tuple

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import xgboost as xgb

# Ensure local package imports work reliably
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from utils import (
    load_and_validate_data,
    preprocess_features,
    evaluate_model,
    plot_confusion_matrix,
    plot_feature_importances,
    save_model_bundle,
    DEFAULT_MODEL_PATH,
    FIGURES_DIR,
)

logger = logging.getLogger("MetroFlow.Train")


def run_leakage_experiment(
    df: pd.DataFrame,
    test_size: float = 0.2,
    random_state: int = 42,
) -> Dict[str, Any]:
    """
    Evaluates and documents the impact of Target Leakage:
    A: Temporal + Station features only (Clean, Leakage-Free)
    B: Temporal + Station + Entries + Exits (Target Leakage Introduced)
    """
    logger.info("=" * 70)
    logger.info("EXPERIMENT: TARGET LEAKAGE EVALUATION")
    logger.info("=" * 70)
    logger.info("Comparing Model A (Clean) vs Model B (With Entries & Exits)...")

    # Experiment A: Clean Features
    X_clean, _, cols_clean = preprocess_features(df, is_training=True, include_leakage_features=False)
    y = df["Congestion_Level"].values
    X_train_c, X_test_c, y_train, y_test = train_test_split(
        X_clean, y, test_size=test_size, random_state=random_state, stratify=y
    )
    
    rf_clean = RandomForestClassifier(n_estimators=40, max_depth=14, random_state=random_state, n_jobs=-1)
    rf_clean.fit(X_train_c, y_train)
    preds_clean = rf_clean.predict(X_test_c)
    metrics_clean = evaluate_model(y_test, preds_clean, model_name="A: Temporal + Station Only (Clean)")

    # Experiment B: Leaked Features (Entries + Exits)
    X_leaked, _, cols_leaked = preprocess_features(df, is_training=True, include_leakage_features=True)
    X_train_l, X_test_l, _, _ = train_test_split(
        X_leaked, y, test_size=test_size, random_state=random_state, stratify=y
    )
    
    rf_leaked = RandomForestClassifier(n_estimators=40, max_depth=14, random_state=random_state, n_jobs=-1)
    rf_leaked.fit(X_train_l, y_train)
    preds_leaked = rf_leaked.predict(X_test_l)
    metrics_leaked = evaluate_model(y_test, preds_leaked, model_name="B: With Entries + Exits (Leaked)")

    leakage_report = (
        "\n" + "=" * 70 + "\n"
        "TARGET LEAKAGE EXPERIMENT RESULTS & FINDINGS\n"
        + "=" * 70 + "\n"
        f"Model A (Clean Features: Temporal + Station):\n"
        f"  - Features ({len(cols_clean)}): {cols_clean}\n"
        f"  - Accuracy: {metrics_clean['accuracy']:.4f} | Weighted F1: {metrics_clean['f1_weighted']:.4f}\n\n"
        f"Model B (Leaked Features: Temporal + Station + Entries + Exits):\n"
        f"  - Features ({len(cols_leaked)}): {cols_leaked}\n"
        f"  - Accuracy: {metrics_leaked['accuracy']:.4f} | Weighted F1: {metrics_leaked['f1_weighted']:.4f}\n\n"
        "WHY ENTRIES AND EXITS INTRODUCE TARGET LEAKAGE:\n"
        "1. In feature engineering, Total_Traffic is computed as Entries + Exits.\n"
        "2. Congestion_Level is defined directly from Total_Traffic quantiles (Low <= Q1, Medium <= Q2, High > Q2).\n"
        "3. When Entries and Exits are fed into the model, the trees learn the exact linear sum (Entries + Exits),\n"
        "   causing artificial near-100% accuracy and massive target leakage.\n"
        "4. In real-world subway operations, future passenger entry/exit numbers are UNKNOWN beforehand.\n"
        "   The platform must predict congestion based strictly on scheduled temporal and station coordinates.\n"
        "CONCLUSION: Exclude Total_Traffic, Entries, and Exits from the production model.\n"
        + "=" * 70
    )
    print(leakage_report)
    
    return {
        "clean_metrics": metrics_clean,
        "leaked_metrics": metrics_leaked,
        "report_text": leakage_report,
    }


def train_and_compare_models(
    df: pd.DataFrame,
    test_size: float = 0.2,
    random_state: int = 42,
) -> Tuple[Dict[str, Any], Dict[str, Any], List[str], Dict[str, Any]]:
    """
    Trains Decision Tree, Random Forest, and XGBoost on clean features.
    Selects and saves the best model.
    """
    logger.info("=" * 70)
    logger.info("PRODUCTION MODEL TRAINING & COMPARISON (CLEAN FEATURES)")
    logger.info("=" * 70)

    # 1. Feature Preprocessing & Target Encoding
    X, encoders, feature_cols = preprocess_features(
        df, is_training=True, include_leakage_features=False
    )
    y_raw = df["Congestion_Level"].values
    
    # Target LabelEncoder for XGBoost compatibility
    target_encoder = LabelEncoder()
    y_encoded = target_encoder.fit_transform(y_raw)
    classes = target_encoder.classes_.tolist()  # ['High', 'Low', 'Medium']
    
    logger.info("Feature Matrix Shape: %s | Target Classes: %s", X.shape, classes)
    logger.info("Selected Input Features (%d): %s", len(feature_cols), feature_cols)

    # 2. Stratified Train-Test Split (80% Train, 20% Test)
    X_train, X_test, y_train_enc, y_test_enc, y_train, y_test = train_test_split(
        X, y_encoded, y_raw, test_size=test_size, random_state=random_state, stratify=y_raw
    )
    logger.info("Training Set: %d samples | Test Set: %d samples", len(X_train), len(X_test))

    models_to_train = {
        "Decision Tree": DecisionTreeClassifier(
            max_depth=16,
            min_samples_split=20,
            min_samples_leaf=10,
            random_state=random_state,
        ),
        "Random Forest": RandomForestClassifier(
            n_estimators=100,
            max_depth=16,
            min_samples_split=10,
            min_samples_leaf=4,
            random_state=random_state,
            n_jobs=-1,
        ),
        "XGBoost": xgb.XGBClassifier(
            n_estimators=100,
            max_depth=7,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=random_state,
            eval_metric="mlogloss",
            n_jobs=-1,
        ),
    }

    results = {}
    fitted_models = {}
    predictions = {}

    for name, clf in models_to_train.items():
        logger.info("Training %s...", name)
        t_start = time.time()
        
        if name == "XGBoost":
            clf.fit(X_train, y_train_enc)
            y_pred_enc = clf.predict(X_test)
            y_pred = target_encoder.inverse_transform(y_pred_enc)
        else:
            clf.fit(X_train, y_train)
            y_pred = clf.predict(X_test)
            
        elapsed = time.time() - t_start
        fitted_models[name] = clf
        predictions[name] = y_pred

        metrics = evaluate_model(y_test, y_pred, model_name=name)
        metrics["training_time_sec"] = round(elapsed, 2)
        results[name] = metrics

    # 3. Model Comparison Table
    print("\n" + "=" * 80)
    print("MODEL PERFORMANCE COMPARISON (CLEAN FEATURES)")
    print("=" * 80)
    header = f"{'Model':<18} | {'Accuracy':<10} | {'F1 (Weighted)':<14} | {'Precision':<10} | {'Recall':<10} | {'Train Time':<10}"
    print(header)
    print("-" * 80)
    for name, m in results.items():
        row = (
            f"{name:<18} | {m['accuracy']:<10.4f} | {m['f1_weighted']:<14.4f} | "
            f"{m['precision_weighted']:<10.4f} | {m['recall_weighted']:<10.4f} | {m['training_time_sec']:<8.2f}s"
        )
        print(row)
    print("=" * 80 + "\n")

    # 4. Automated Model Selection (based on highest weighted F1 score)
    best_name = max(results, key=lambda k: results[k]["f1_weighted"])
    best_model = fitted_models[best_name]
    best_metrics = results[best_name]
    best_preds = predictions[best_name]

    print(f"AUTOMATED SELECTION: '{best_name}' achieved the best F1 Score ({best_metrics['f1_weighted']:.4f}).")
    print("\nCLASSIFICATION REPORT FOR BEST MODEL:")
    print(best_metrics["classification_report"])

    # 5. Feature Importance Extraction & Ranking
    if hasattr(best_model, "feature_importances_"):
        importances = dict(zip(feature_cols, [float(x) for x in best_model.feature_importances_]))
    else:
        importances = {}

    print("\n" + "=" * 60)
    print("FEATURE IMPORTANCE RANKINGS (BEST MODEL)")
    print("=" * 60)
    sorted_importances = sorted(importances.items(), key=lambda x: x[1], reverse=True)
    for rank, (feat, score) in enumerate(sorted_importances, start=1):
        print(f"{rank:2d}. {feat:<22} : {score * 100:6.2f}%")
    print("=" * 60)

    # Explanation of top drivers
    top_3 = [x[0] for x in sorted_importances[:3]]
    print(
        f"\nINTERPRETATION: The top features driving subway congestion prediction are {top_3}.\n"
        "- 'hour' strongly determines rush hour peaks (8-9 AM, 5-7 PM) versus night/early morning lulls.\n"
        "- 'Latitude' & 'Longitude' represent station geospatial hub positioning (e.g. Midtown/Financial District vs outer terminals).\n"
        "- 'Stop Name' & 'Borough' capture station-specific passenger interchange patterns.\n"
    )

    # 6. Save Plots
    cm_path = os.path.join(FIGURES_DIR, "confusion_matrix.png")
    fi_path = os.path.join(FIGURES_DIR, "feature_importance.png")
    
    cm_matrix = np.array(best_metrics["confusion_matrix"])
    plot_confusion_matrix(
        cm_matrix,
        classes=["Low", "Medium", "High"],
        title=f"Confusion Matrix - {best_name}",
        output_path=cm_path,
    )
    plot_feature_importances(
        importances,
        title=f"Feature Importances - {best_name}",
        output_path=fi_path,
    )

    # 7. Persist Best Model Bundle
    bundle = {
        "model": best_model,
        "model_name": best_name,
        "encoders": encoders,
        "target_encoder": target_encoder if best_name == "XGBoost" else None,
        "feature_cols": feature_cols,
        "target_classes": classes,
        "metrics": best_metrics,
        "importances": importances,
        "all_comparison_results": results,
    }
    save_model_bundle(bundle, DEFAULT_MODEL_PATH)
    print(f"\nModel artifact saved successfully to: {DEFAULT_MODEL_PATH}")

    return bundle, results, feature_cols, importances


def main():
    parser = argparse.ArgumentParser(description="Train AI MetroFlow Congestion Prediction Models")
    parser.add_argument(
        "--data-path",
        type=str,
        default=None,
        help="Optional custom path to features.csv",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=150000,
        help="Number of records to sample for training (default: 150000; set 0 for full data)",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Train on the full 4.58M dataset (requires high RAM)",
    )
    parser.add_argument(
        "--random-state",
        type=int,
        default=42,
        help="Random seed for reproducibility",
    )
    args = parser.parse_args()

    sample_size = None if args.full or args.sample_size == 0 else args.sample_size

    # Step 1: Load and Validate Data
    df, summary = load_and_validate_data(
        filepath=args.data_path,
        sample_size=sample_size,
        random_state=args.random_state,
    )

    # Step 2: Target Leakage Experiment
    run_leakage_experiment(df, random_state=args.random_state)

    # Step 3: Production Model Training & Selection
    train_and_compare_models(df, random_state=args.random_state)


if __name__ == "__main__":
    main()