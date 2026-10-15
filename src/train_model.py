"""
AI MetroFlow - Machine Learning Model Training & Evaluation Pipeline
Trains and compares Logistic Regression, Decision Tree, Random Forest,
Gradient Boosting, AdaBoost, and XGBoost classifiers on subway Congestion_Level.
Performs target leakage analysis, multi-model benchmarking, and automatically persists the best model.
"""

import os
import sys
import time
import argparse
import logging
from typing import Dict, Any, List, Tuple

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import (
    RandomForestClassifier,
    GradientBoostingClassifier,
    AdaBoostClassifier,
)
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.pipeline import make_pipeline

try:
    import xgboost as xgb
    HAS_XGB = True
except ImportError:
    HAS_XGB = False

# Ensure local package imports work reliably
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

ROOT_DIR = os.path.dirname(current_dir)
REPORTS_DIR = os.path.join(ROOT_DIR, "reports")
FIGURES_DIR = os.path.join(REPORTS_DIR, "figures")
COMPARISON_CSV_PATH = os.path.join(REPORTS_DIR, "model_comparison.csv")
COMPARISON_FIG_PATH = os.path.join(FIGURES_DIR, "model_comparison.png")

from utils import (
    load_and_validate_data,
    preprocess_features,
    evaluate_model,
    plot_confusion_matrix,
    plot_feature_importances,
    save_model_bundle,
    DEFAULT_MODEL_PATH,
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


def plot_model_comparison(comparison_df: pd.DataFrame, output_path: str):
    """
    Generates a high-resolution comparison chart with Accuracy and F1 Score subplots.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Sort for visual hierarchy
    df_sorted = comparison_df.sort_values(by="F1 Score", ascending=True)
    models = df_sorted["Model"].tolist()
    accuracies = [a * 100 for a in df_sorted["Accuracy"]]
    f1_scores = df_sorted["F1 Score"].tolist()
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6), sharey=True)
    
    # 1. Accuracy Subplot
    bars1 = ax1.barh(models, accuracies, color="#3B82F6", edgecolor="#1E3A8A", height=0.55)
    bars1[-1].set_color("#1E3A8A")  # Highlight top model
    ax1.set_xlabel("Accuracy (%)", fontsize=11, fontweight="bold")
    ax1.set_title("Model Accuracy Benchmark", fontsize=13, fontweight="bold", pad=12)
    ax1.set_xlim(0, 105)
    for bar in bars1:
        w = bar.get_width()
        ax1.text(w + 1.0, bar.get_y() + bar.get_height() / 2, f"{w:.2f}%",
                 ha="left", va="center", fontsize=9.5, fontweight="bold", color="#1F2937")
    ax1.grid(axis="x", linestyle="--", alpha=0.5)
    
    # 2. F1 Score Subplot
    bars2 = ax2.barh(models, f1_scores, color="#10B981", edgecolor="#065F46", height=0.55)
    bars2[-1].set_color("#059669")  # Highlight top model
    ax2.set_xlabel("Weighted F1 Score", fontsize=11, fontweight="bold")
    ax2.set_title("Model F1 Score Benchmark", fontsize=13, fontweight="bold", pad=12)
    ax2.set_xlim(0, 1.05)
    for bar in bars2:
        w = bar.get_width()
        ax2.text(w + 0.015, bar.get_y() + bar.get_height() / 2, f"{w:.4f}",
                 ha="left", va="center", fontsize=9.5, fontweight="bold", color="#1F2937")
    ax2.grid(axis="x", linestyle="--", alpha=0.5)
    
    plt.suptitle("AI MetroFlow: Multi-Model Benchmark Comparison (NYC Subway Transit)",
                 fontsize=15, fontweight="bold", y=1.02)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
    logger.info("Saved model comparison plot to: %s", output_path)


def train_and_compare_models(
    df: pd.DataFrame,
    test_size: float = 0.2,
    random_state: int = 42,
) -> Tuple[Dict[str, Any], pd.DataFrame, List[str], Dict[str, Any]]:
    """
    Trains and benchmarks 6 classification models on clean, leakage-free features:
    1. Logistic Regression
    2. Decision Tree Classifier
    3. Random Forest Classifier
    4. Gradient Boosting Classifier
    5. AdaBoost Classifier
    6. XGBoost Classifier (if available)

    Saves comparison CSV, visualization plots, and automatically persists the best model.
    """
    logger.info("=" * 80)
    logger.info("MULTI-MODEL BENCHMARKING & COMPARISON PIPELINE")
    logger.info("=" * 80)

    # 1. Feature Preprocessing & Target Encoding
    X, encoders, feature_cols = preprocess_features(
        df, is_training=True, include_leakage_features=False
    )
    y_raw = df["Congestion_Level"].values
    
    # Target LabelEncoder for XGBoost and consistency
    target_encoder = LabelEncoder()
    y_encoded = target_encoder.fit_transform(y_raw)
    classes = target_encoder.classes_.tolist()  # ['High', 'Low', 'Medium']
    
    logger.info("Feature Matrix Shape: %s | Target Classes: %s", X.shape, classes)
    logger.info("Selected Input Features (%d): %s", len(feature_cols), feature_cols)

    # 2. Stratified Train-Test Split (80% Train, 20% Test) - Identical for all models
    X_train, X_test, y_train_enc, y_test_enc, y_train, y_test = train_test_split(
        X, y_encoded, y_raw, test_size=test_size, random_state=random_state, stratify=y_raw
    )
    logger.info("Training Set: %d samples | Test Set: %d samples", len(X_train), len(X_test))

    # 3. Model Zoo Definition
    models_to_train: Dict[str, Any] = {
        "Logistic Regression": make_pipeline(
            StandardScaler(),
            LogisticRegression(max_iter=1000, random_state=random_state)
        ),
        "Decision Tree Classifier": DecisionTreeClassifier(
            max_depth=16,
            min_samples_split=20,
            min_samples_leaf=10,
            random_state=random_state,
        ),
        "Random Forest Classifier": RandomForestClassifier(
            n_estimators=100,
            max_depth=16,
            min_samples_split=10,
            min_samples_leaf=4,
            random_state=random_state,
            n_jobs=-1,
        ),
        "Gradient Boosting Classifier": GradientBoostingClassifier(
            n_estimators=50,
            max_depth=5,
            learning_rate=0.1,
            subsample=0.8,
            random_state=random_state,
        ),
        "AdaBoost Classifier": AdaBoostClassifier(
            n_estimators=50,
            learning_rate=0.1,
            random_state=random_state,
        ),
    }

    if HAS_XGB:
        models_to_train["XGBoost Classifier"] = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=7,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=random_state,
            eval_metric="mlogloss",
            n_jobs=-1,
        )

    results: Dict[str, Any] = {}
    fitted_models: Dict[str, Any] = {}
    predictions: Dict[str, np.ndarray] = {}

    # 4. Train and Evaluate each Model
    for name, clf in models_to_train.items():
        logger.info("--> Training [%s]...", name)
        t_start = time.time()
        
        if "XGBoost" in name:
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
        logger.info(
            "    Completed in %.2fs | Accuracy: %.4f | Weighted F1: %.4f",
            elapsed, metrics["accuracy"], metrics["f1_weighted"]
        )

    # 5. Build Model Comparison DataFrame
    comparison_rows = []
    for name, m in results.items():
        comparison_rows.append({
            "Model": name,
            "Accuracy": round(float(m["accuracy"]), 4),
            "Precision": round(float(m["precision_weighted"]), 4),
            "Recall": round(float(m["recall_weighted"]), 4),
            "F1 Score": round(float(m["f1_weighted"]), 4),
        })

    comparison_df = (
        pd.DataFrame(comparison_rows)
        .sort_values(by="F1 Score", ascending=False)
        .reset_index(drop=True)
    )

    # 6. Save Comparison CSV (reports/model_comparison.csv)
    os.makedirs(REPORTS_DIR, exist_ok=True)
    comparison_df.to_csv(COMPARISON_CSV_PATH, index=False)
    logger.info("Saved model comparison CSV to: %s", COMPARISON_CSV_PATH)

    # 7. Print Model Comparison Table
    print("\n" + "=" * 90)
    print("AI METROFLOW: MULTI-MODEL BENCHMARKING RESULTS")
    print("=" * 90)
    header = f"{'Rank':<5} | {'Model':<30} | {'Accuracy':<10} | {'Precision':<10} | {'Recall':<10} | {'F1 Score':<10}"
    print(header)
    print("-" * 90)
    for rank, row in comparison_df.iterrows():
        print(
            f"{rank + 1:<5} | {row['Model']:<30} | {row['Accuracy']:<10.4f} | "
            f"{row['Precision']:<10.4f} | {row['Recall']:<10.4f} | {row['F1 Score']:<10.4f}"
        )
    print("=" * 90)

    # 8. Generate Visualizations (reports/figures/model_comparison.png)
    plot_model_comparison(comparison_df, COMPARISON_FIG_PATH)

    # 9. Automated Best Model Selection (by Highest F1 Score)
    best_row = comparison_df.iloc[0]
    best_name = best_row["Model"]
    best_acc = best_row["Accuracy"]
    best_f1 = best_row["F1 Score"]
    best_model = fitted_models[best_name]
    best_metrics = results[best_name]

    print("\n" + "=" * 70)
    print("AUTOMATIC BEST MODEL SELECTION (HIGHEST F1 SCORE)")
    print("=" * 70)
    print(f"Best Model:    {best_name}")
    print(f"Best Accuracy: {best_acc:.4f} ({best_acc * 100:.2f}%)")
    print(f"Best F1:       {best_f1:.4f}")
    print("=" * 70 + "\n")

    # 10. Extract Feature Importances if available
    if hasattr(best_model, "feature_importances_"):
        importances = dict(zip(feature_cols, [float(x) for x in best_model.feature_importances_]))
    elif hasattr(best_model, "named_steps") and hasattr(best_model.named_steps.get("logisticregression", None), "coef_"):
        coef_mean = np.mean(np.abs(best_model.named_steps["logisticregression"].coef_), axis=0)
        importances = dict(zip(feature_cols, [float(x) for x in coef_mean]))
    else:
        rf_clf = fitted_models.get("Random Forest Classifier", None)
        if rf_clf and hasattr(rf_clf, "feature_importances_"):
            importances = dict(zip(feature_cols, [float(x) for x in rf_clf.feature_importances_]))
        else:
            importances = {}

    # Save Confusion Matrix & Feature Importance plots for best model
    cm_path = os.path.join(FIGURES_DIR, "confusion_matrix.png")
    fi_path = os.path.join(FIGURES_DIR, "feature_importance.png")
    
    cm_matrix = np.array(best_metrics["confusion_matrix"])
    plot_confusion_matrix(
        cm_matrix,
        classes=["Low", "Medium", "High"],
        title=f"Confusion Matrix - {best_name}",
        output_path=cm_path,
    )
    if importances:
        plot_feature_importances(
            importances,
            title=f"Feature Importances - {best_name}",
            output_path=fi_path,
        )

    # 11. Persist Best Model Bundle & Benchmark Registry
    bundle = {
        "model": best_model,
        "model_name": best_name,
        "encoders": encoders,
        "target_encoder": target_encoder if "XGBoost" in best_name else None,
        "feature_cols": feature_cols,
        "target_classes": classes,
        "metrics": best_metrics,
        "importances": importances,
        "all_comparison_results": results,
        "comparison_df": comparison_df.to_dict(orient="records"),
    }
    save_model_bundle(bundle, DEFAULT_MODEL_PATH)
    compat_path = os.path.join(os.path.dirname(DEFAULT_MODEL_PATH), "model.pkl")
    save_model_bundle(bundle, compat_path)
    print(f"Model artifact bundle saved successfully to: {DEFAULT_MODEL_PATH}")

    return bundle, comparison_df, feature_cols, importances


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