"""
AI MetroFlow - Passenger Demand Forecasting Module
Trains Random Forest and XGBoost regressors to predict continuous passenger volume (Total_Traffic),
evaluates R², RMSE, MAE, selects the champion, and provides multi-horizon ridership forecasts
(Next 1 Hour, Next 3 Hours, Next 24 Hours) translated into future congestion tiers.
"""

import os
import sys
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple, Optional

import numpy as np
import pandas as pd
import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

try:
    import xgboost as xgb
    HAS_XGB = True
except ImportError:
    HAS_XGB = False

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("MetroFlow.DemandForecast")

# Directory paths
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(CURRENT_DIR)
MODELS_DIR = os.path.join(ROOT_DIR, "models")
REPORTS_DIR = os.path.join(ROOT_DIR, "reports")
FIGURES_DIR = os.path.join(REPORTS_DIR, "figures")
STATIONS_CSV = os.path.join(ROOT_DIR, "data", "stations.csv")
DEMAND_MODEL_PATH = os.path.join(MODELS_DIR, "demand_model.pkl")
FORECAST_CSV_PATH = os.path.join(REPORTS_DIR, "forecast_results.csv")
FORECAST_FIG_PATH = os.path.join(FIGURES_DIR, "demand_forecast.png")

# Data search paths
POTENTIAL_DATA_PATHS = [
    os.path.join(ROOT_DIR, "data", "features.csv"),
    r"C:\Users\WaterMelon\OneDrive\Desktop\SpringBoard\MetroFlow\data\features.csv",
    os.path.join("..", "MetroFlow", "data", "features.csv"),
]

# Production non-leaked feature schema
FEATURE_COLS = [
    "hour", "day", "month", "year", "day_of_week",
    "is_weekend", "is_peak_hour", "Latitude", "Longitude",
    "Borough_encoded", "Structure_encoded", "Stop Name_encoded"
]


def resolve_data_path() -> str:
    """Finds existing path to raw subway features dataset."""
    for p in POTENTIAL_DATA_PATHS:
        if os.path.exists(p):
            return p
    raise FileNotFoundError("features.csv could not be located in any standard project path.")


def load_and_preprocess_demand_data(
    sample_size: int = 50000,
    random_state: int = 42
) -> Tuple[pd.DataFrame, pd.Series, Dict[str, LabelEncoder], Dict[str, float]]:
    """
    Loads features.csv and prepares production-safe training data for Total_Traffic.
    Strictly excludes target leakage: Entries, Exits, Congestion_Level are NOT in features.
    """
    filepath = resolve_data_path()
    logger.info("Loading dataset from %s (sampling %d records)...", filepath, sample_size)
    df = pd.read_csv(filepath, nrows=sample_size)

    # Clean target
    df["Total_Traffic"] = pd.to_numeric(df["Total_Traffic"], errors="coerce").fillna(0)
    df = df[df["Total_Traffic"] >= 0].copy()

    # Calculate target quantiles for future congestion tier conversion
    low_med_thresh = float(df["Total_Traffic"].quantile(0.33))
    med_high_thresh = float(df["Total_Traffic"].quantile(0.66))
    thresholds = {
        "low_med": round(low_med_thresh, 1),
        "med_high": round(med_high_thresh, 1),
    }
    logger.info("Computed target congestion thresholds: Low-Med=%.1f, Med-High=%.1f", low_med_thresh, med_high_thresh)

    # Encode categoricals
    encoders = {}
    for col in ["Borough", "Structure", "Stop Name"]:
        le = LabelEncoder()
        df[col + "_encoded"] = le.fit_transform(df[col].astype(str))
        encoders[col] = le

    X = df[FEATURE_COLS].copy()
    y = df["Total_Traffic"].copy()

    return X, y, encoders, thresholds


def train_and_benchmark_regressors(
    X: pd.DataFrame,
    y: pd.Series,
    test_size: float = 0.2,
    random_state: int = 42
) -> Tuple[Any, str, pd.DataFrame, Dict[str, Any], np.ndarray, np.ndarray]:
    """
    Trains and benchmarks Random Forest Regressor and XGBoost Regressor.
    Returns best model, best model name, comparison dataframe, and test metrics.
    """
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )
    logger.info("Train set: %d samples, Test set: %d samples", len(X_train), len(X_test))

    results = []
    models = {}
    predictions = {}

    # 1. Random Forest Regressor
    logger.info("Training Random Forest Regressor...")
    t0 = time.time()
    rf = RandomForestRegressor(
        n_estimators=50,
        max_depth=16,
        min_samples_split=8,
        n_jobs=-1,
        random_state=random_state
    )
    rf.fit(X_train, y_train)
    rf_time = time.time() - t0
    rf_pred = rf.predict(X_test)
    models["Random Forest Regressor"] = rf
    predictions["Random Forest Regressor"] = rf_pred

    rf_r2 = float(r2_score(y_test, rf_pred))
    rf_rmse = float(np.sqrt(mean_squared_error(y_test, rf_pred)))
    rf_mae = float(mean_absolute_error(y_test, rf_pred))
    results.append({
        "Model": "Random Forest Regressor",
        "R²": round(rf_r2, 4),
        "RMSE": round(rf_rmse, 2),
        "MAE": round(rf_mae, 2),
        "Train_Time_Sec": round(rf_time, 2),
    })
    logger.info("Random Forest - R²: %.4f, RMSE: %.2f, MAE: %.2f (%.2fs)", rf_r2, rf_rmse, rf_mae, rf_time)

    # 2. XGBoost Regressor
    if HAS_XGB:
        logger.info("Training XGBoost Regressor...")
        t0 = time.time()
        xgb_reg = xgb.XGBRegressor(
            n_estimators=80,
            max_depth=6,
            learning_rate=0.08,
            subsample=0.8,
            colsample_bytree=0.8,
            n_jobs=-1,
            random_state=random_state
        )
        xgb_reg.fit(X_train, y_train)
        xgb_time = time.time() - t0
        xgb_pred = xgb_reg.predict(X_test)
        models["XGBoost Regressor"] = xgb_reg
        predictions["XGBoost Regressor"] = xgb_pred

        xgb_r2 = float(r2_score(y_test, xgb_pred))
        xgb_rmse = float(np.sqrt(mean_squared_error(y_test, xgb_pred)))
        xgb_mae = float(mean_absolute_error(y_test, xgb_pred))
        results.append({
            "Model": "XGBoost Regressor",
            "R²": round(xgb_r2, 4),
            "RMSE": round(xgb_rmse, 2),
            "MAE": round(xgb_mae, 2),
            "Train_Time_Sec": round(xgb_time, 2),
        })
        logger.info("XGBoost - R²: %.4f, RMSE: %.2f, MAE: %.2f (%.2fs)", xgb_r2, xgb_rmse, xgb_mae, xgb_time)

    comparison_df = pd.DataFrame(results).sort_values(by="R²", ascending=False).reset_index(drop=True)

    # Automated champion selection based on highest R²
    best_row = comparison_df.iloc[0]
    best_name = best_row["Model"]
    best_model = models[best_name]
    logger.info("🏆 Selected Champion Regressor: %s (R²=%.4f, RMSE=%.2f)", best_name, best_row["R²"], best_row["RMSE"])

    test_payload = {
        "y_test": y_test.values,
        "best_pred": predictions[best_name],
        "comparison_df": comparison_df,
    }

    return best_model, best_name, comparison_df, test_payload, X_test.values, y_test.values


def traffic_to_congestion_tier(volume: float, thresholds: Dict[str, float]) -> str:
    """Converts continuous ridership volume into operational congestion tiers."""
    if volume > thresholds["med_high"]:
        return "High"
    elif volume > thresholds["low_med"]:
        return "Medium"
    else:
        return "Low"


def generate_multi_horizon_forecast(
    model: Any,
    encoders: Dict[str, LabelEncoder],
    thresholds: Dict[str, float],
    stations_df: pd.DataFrame,
    start_time: Optional[datetime] = None,
    horizons: List[int] = [1, 3, 24]
) -> pd.DataFrame:
    """
    Generates multi-horizon passenger demand forecasts across all stations.
    Horizons: Next 1 Hour (1h), Next 3 Hours (3h), Next 24 Hours (24h).
    """
    if start_time is None:
        start_time = datetime.now().replace(minute=0, second=0, microsecond=0)

    max_horizon = max(horizons)
    forecast_rows = []

    for step in range(1, max_horizon + 1):
        future_dt = start_time + timedelta(hours=step)
        f_hour = future_dt.hour
        f_day = future_dt.day
        f_month = future_dt.month
        f_year = future_dt.year
        f_dow = future_dt.weekday()
        f_weekend = 1 if f_dow >= 5 else 0
        f_peak = 1 if (7 <= f_hour <= 9 or 16 <= f_hour <= 19) and not f_weekend else 0

        # Build feature dataframe for all stations at this future step
        step_df = stations_df.copy()
        step_df["hour"] = f_hour
        step_df["day"] = f_day
        step_df["month"] = f_month
        step_df["year"] = f_year
        step_df["day_of_week"] = f_dow
        step_df["is_weekend"] = f_weekend
        step_df["is_peak_hour"] = f_peak

        for col in ["Borough", "Structure", "Stop Name"]:
            enc_col = f"{col}_encoded"
            le = encoders.get(col)
            if le is not None:
                known_classes = set(le.classes_)
                step_df[enc_col] = step_df[col].apply(
                    lambda v: int(le.transform([v])[0]) if v in known_classes else 0
                )
            else:
                step_df[enc_col] = 0

        X_step = step_df[FEATURE_COLS]
        pred_traffic = model.predict(X_step)
        pred_traffic = np.clip(pred_traffic, 0, None)  # Volume cannot be negative

        for idx, (_, row) in enumerate(step_df.iterrows()):
            vol = round(float(pred_traffic[idx]), 1)
            tier = traffic_to_congestion_tier(vol, thresholds)

            # Map operational recommendation
            if tier == "High":
                rec_action = "Deploy standby trains & surge frequency (Every 2 min)"
            elif tier == "Medium":
                rec_action = "Maintain active headway monitoring (Every 5 min)"
            else:
                rec_action = "Nominal transit schedule sufficient (Every 10 min)"

            # Assign matching horizon tags
            horizon_tags = []
            if step <= 1:
                horizon_tags.append("Next 1 Hour")
            if step <= 3:
                horizon_tags.append("Next 3 Hours")
            if step <= 24:
                horizon_tags.append("Next 24 Hours")

            for h_tag in horizon_tags:
                forecast_rows.append({
                    "Horizon": h_tag,
                    "Hour_Ahead": step,
                    "Forecast_Timestamp": future_dt.strftime("%Y-%m-%d %H:%M:%S"),
                    "Hour": f_hour,
                    "Stop Name": row["Stop Name"],
                    "Borough": row["Borough"],
                    "Structure": row["Structure"],
                    "Latitude": float(row["Latitude"]),
                    "Longitude": float(row["Longitude"]),
                    "Forecasted_Ridership": vol,
                    "Predicted_Congestion": tier,
                    "Recommended_Action": rec_action,
                })

    forecast_df = pd.DataFrame(forecast_rows)
    return forecast_df


def plot_demand_forecast(
    y_test: np.ndarray,
    y_pred: np.ndarray,
    forecast_df: pd.DataFrame,
    save_path: str = FORECAST_FIG_PATH
):
    """
    Renders high-resolution publication plot for Demand Forecasting Center:
    1. Actual vs. Forecasted Ridership scatter / regression fit.
    2. 24-Hour Network Demand Trend Curve with peak commuter windows.
    3. Borough Demand Comparison Bar Chart.
    """
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(18, 5.5))

    # Panel 1: Actual vs Forecasted
    sample_idx = np.random.choice(len(y_test), size=min(1200, len(y_test)), replace=False)
    ax1.scatter(y_test[sample_idx], y_pred[sample_idx], alpha=0.35, color="#2563EB", edgecolors="none", s=25)
    max_val = max(np.percentile(y_test, 99), np.percentile(y_pred, 99))
    ax1.plot([0, max_val], [0, max_val], "r--", linewidth=2, label="Ideal 1:1 Parity")
    ax1.set_xlim(0, max_val)
    ax1.set_ylim(0, max_val)
    ax1.set_title("A. Actual vs. Forecasted Ridership", fontsize=12, fontweight="bold")
    ax1.set_xlabel("Actual Total Traffic (Passengers/hr)")
    ax1.set_ylabel("Predicted Demand (Passengers/hr)")
    ax1.legend()
    ax1.grid(True, linestyle="--", alpha=0.3)

    # Panel 2: 24-Hour Diurnal Demand Curve
    df_24h = forecast_df[forecast_df["Horizon"] == "Next 24 Hours"].drop_duplicates(
        subset=["Hour_Ahead", "Stop Name"]
    )
    hourly_curve = df_24h.groupby("Hour_Ahead")["Forecasted_Ridership"].mean().reset_index()

    ax2.plot(hourly_curve["Hour_Ahead"], hourly_curve["Forecasted_Ridership"], "o-", color="#059669", linewidth=2.5, markersize=5)
    ax2.set_title("B. 24-Hour Network Demand Projection", fontsize=12, fontweight="bold")
    ax2.set_xlabel("Hours Ahead (t + 1 to t + 24)")
    ax2.set_ylabel("Mean Projected Ridership per Station")
    ax2.grid(True, linestyle="--", alpha=0.3)

    # Panel 3: Borough Demand Comparison
    borough_agg = df_24h.groupby("Borough")["Forecasted_Ridership"].sum().reset_index()
    borough_agg = borough_agg.sort_values(by="Forecasted_Ridership", ascending=False)
    sns.barplot(data=borough_agg, x="Borough", y="Forecasted_Ridership", palette="Blues_r", ax=ax3)
    ax3.set_title("C. Projected Ridership by Borough", fontsize=12, fontweight="bold")
    ax3.set_xlabel("Borough")
    ax3.set_ylabel("Aggregated Ridership (Next 24h)")
    ax3.grid(axis="y", linestyle="--", alpha=0.3)

    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    plt.close()
    logger.info("Saved forecast visualization to: %s", save_path)


def save_demand_bundle(
    model: Any,
    model_name: str,
    comparison_df: pd.DataFrame,
    encoders: Dict[str, LabelEncoder],
    thresholds: Dict[str, float],
    save_path: str = DEMAND_MODEL_PATH
):
    """Persists champion demand forecasting model and metadata bundle."""
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    bundle = {
        "model": model,
        "model_name": model_name,
        "benchmark_df": comparison_df,
        "feature_cols": FEATURE_COLS,
        "encoders": encoders,
        "thresholds": thresholds,
        "trained_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    joblib.dump(bundle, save_path)
    logger.info("Saved champion demand forecasting bundle to: %s", save_path)


def run_pipeline() -> Dict[str, Any]:
    """Executes end-to-end demand forecasting training, evaluation, and multi-horizon projection."""
    logger.info("=================================================================")
    logger.info("AI MetroFlow: Passenger Demand Forecasting Pipeline")
    logger.info("=================================================================")

    # 1. Load Data
    X, y, encoders, thresholds = load_and_preprocess_demand_data(sample_size=60000)

    # 2. Train and benchmark regressors
    best_model, best_name, comp_df, test_payload, _, _ = train_and_benchmark_regressors(X, y)

    # 3. Save Model Bundle
    save_demand_bundle(best_model, best_name, comp_df, encoders, thresholds)

    # 4. Load Stations Database for Projections
    if os.path.exists(STATIONS_CSV):
        stations_df = pd.read_csv(STATIONS_CSV)
    else:
        logger.warning("data/stations.csv not found; extracting unique stations from features...")
        raw_df = pd.read_csv(resolve_data_path(), usecols=["Stop Name", "Borough", "Structure", "Latitude", "Longitude"])
        stations_df = raw_df.drop_duplicates(subset=["Stop Name", "Borough"]).reset_index(drop=True)
        b_map = {"M": "Manhattan", "Bk": "Brooklyn", "Q": "Queens", "Bx": "Bronx", "SI": "Staten Island"}
        stations_df["Borough"] = stations_df["Borough"].map(lambda x: b_map.get(x, x))

    # 5. Multi-Horizon Projections
    logger.info("Generating multi-horizon projections across %d stations...", len(stations_df))
    forecast_df = generate_multi_horizon_forecast(
        model=best_model,
        encoders=encoders,
        thresholds=thresholds,
        stations_df=stations_df,
        start_time=datetime.now().replace(minute=0, second=0, microsecond=0),
        horizons=[1, 3, 24]
    )

    # 6. Export Forecast CSV
    os.makedirs(os.path.dirname(FORECAST_CSV_PATH), exist_ok=True)
    forecast_df.to_csv(FORECAST_CSV_PATH, index=False)
    logger.info("Exported multi-horizon forecast results to: %s (%d records)", FORECAST_CSV_PATH, len(forecast_df))

    # 7. Render & Export Figures
    plot_demand_forecast(
        y_test=test_payload["y_test"],
        y_pred=test_payload["best_pred"],
        forecast_df=forecast_df,
        save_path=FORECAST_FIG_PATH
    )

    logger.info("=================================================================")
    logger.info("Demand Forecasting Pipeline Completed Successfully!")
    logger.info("=================================================================")

    return {
        "champion": best_name,
        "comparison_df": comp_df,
        "thresholds": thresholds,
        "forecast_records": len(forecast_df),
    }


if __name__ == "__main__":
    run_pipeline()
