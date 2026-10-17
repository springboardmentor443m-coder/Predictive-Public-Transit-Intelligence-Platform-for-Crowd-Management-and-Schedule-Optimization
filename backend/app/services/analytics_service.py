
from functools import lru_cache

import pandas as pd

from app.services.crowd_service import (
    load_ridership_data,
    get_station_ridership,
    get_peak_period_ridership,
    get_station_hour_hotspots,
    get_station_flow,
)


# ---------------------------------------------------------
# SHARED HISTORICAL DATA
# ---------------------------------------------------------

@lru_cache(maxsize=1)
def _load_analytics_data():
    """Load historical station-hour ridership data."""
    df = load_ridership_data().copy()

    required = {"Date", "Hour", "Station", "Ridership"}
    missing = required - set(df.columns)

    if missing:
        raise ValueError(
            "Ridership dataset is missing columns: "
            + ", ".join(sorted(missing))
        )

    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["Hour"] = pd.to_numeric(df["Hour"], errors="coerce")
    df["Ridership"] = pd.to_numeric(
        df["Ridership"], errors="coerce"
    )

    df = df.dropna(
        subset=["Date", "Hour", "Station", "Ridership"]
    )

    df["Hour"] = df["Hour"].astype(int)
    df = df[df["Hour"].between(0, 23)]

    return df


# ---------------------------------------------------------
# MODEL FEATURE IMPORTANCE
# ---------------------------------------------------------

def _get_feature_importance(model, limit=10):
    """
    Return the highest model feature-importance values.

    These scores describe model-specific predictive patterns.
    They do not establish causation.
    """
    importances = getattr(model, "feature_importances_", None)
    feature_names = getattr(model, "feature_names_in_", None)

    if importances is None or feature_names is None:
        return []

    if len(importances) != len(feature_names):
        return []

    ranked = sorted(
        zip(feature_names, importances),
        key=lambda item: float(item[1]),
        reverse=True,
    )[:limit]

    return [
        {
            "feature": str(name),
            "importance": round(float(score), 6),
        }
        for name, score in ranked
    ]


# ---------------------------------------------------------
# ANALYTICS OVERVIEW
# ---------------------------------------------------------

def get_analytics_overview():
    """Return summary statistics for the historical dataset."""
    df = _load_analytics_data()

    daily = (
        df.groupby("Date")["Ridership"]
        .sum()
        .sort_index()
    )

    hourly = (
        df.groupby("Hour")["Ridership"]
        .sum()
        .sort_values(ascending=False)
    )

    station_totals = (
        df.groupby("Station")["Ridership"]
        .sum()
        .sort_values(ascending=False)
    )

    peak_hour = int(hourly.index[0]) if not hourly.empty else None

    return {
        "data_source": "historical_csv",
        "analysis_type": "historical_ridership_analytics",
        "stations_covered": int(df["Station"].nunique()),
        "observation_rows": int(len(df)),
        "start_date": (
            df["Date"].min().strftime("%Y-%m-%d")
            if not df.empty else None
        ),
        "end_date": (
            df["Date"].max().strftime("%Y-%m-%d")
            if not df.empty else None
        ),
        "total_recorded_ridership": int(df["Ridership"].sum()),
        "average_daily_recorded_ridership": (
            round(float(daily.mean()), 2)
            if not daily.empty else None
        ),
        "busiest_hour": peak_hour,
        "busiest_hour_total_ridership": (
            int(hourly.iloc[0]) if not hourly.empty else None
        ),
        "highest_ridership_station": (
            str(station_totals.index[0])
            if not station_totals.empty else None
        ),
        "highest_ridership_station_total": (
            int(station_totals.iloc[0])
            if not station_totals.empty else None
        ),
        "interpretation_note": (
            "Statistics summarize the available historical station-hour "
            "dataset. They are not live passenger counts."
        ),
    }


# ---------------------------------------------------------
# RIDERSHIP TRENDS
# ---------------------------------------------------------

def get_analytics_ridership_trends():
    """Return daily, hourly, and peak-period historical trends."""
    df = _load_analytics_data()

    daily = (
        df.groupby("Date")["Ridership"]
        .sum()
        .reset_index()
        .sort_values("Date")
    )

    daily["Date"] = daily["Date"].dt.strftime("%Y-%m-%d")

    hourly = (
        df.groupby("Hour")["Ridership"]
        .sum()
        .reset_index()
        .sort_values("Hour")
    )

    return {
        "daily_trends": daily.to_dict(orient="records"),
        "hourly_trends": hourly.to_dict(orient="records"),
        "peak_periods": get_peak_period_ridership(),
        "station_ridership": get_station_ridership(),
        "data_source": "historical_csv",
    }


# ---------------------------------------------------------
# STATION-HOUR ANOMALY ANALYSIS
# ---------------------------------------------------------

def get_ridership_anomalies(limit=100):
    """
    Identify unusual aggregated station-hour ridership values
    using station-specific interquartile ranges.

    This is statistical screening, not a trained anomaly model.
    """
    if not 1 <= limit <= 1000:
        raise ValueError("limit must be between 1 and 1000.")

    df = _load_analytics_data()

    station_hour = (
        df.groupby(["Station", "Hour"])["Ridership"]
        .sum()
        .reset_index()
    )

    station_hour["Q1"] = (
        station_hour.groupby("Station")["Ridership"]
        .transform(lambda values: values.quantile(0.25))
    )

    station_hour["Q3"] = (
        station_hour.groupby("Station")["Ridership"]
        .transform(lambda values: values.quantile(0.75))
    )

    station_hour["IQR"] = (
        station_hour["Q3"] - station_hour["Q1"]
    )

    station_hour["Lower Bound"] = (
        station_hour["Q1"] - 1.5 * station_hour["IQR"]
    ).clip(lower=0)

    station_hour["Upper Bound"] = (
        station_hour["Q3"] + 1.5 * station_hour["IQR"]
    )

    station_hour["Anomaly Type"] = "Normal"

    station_hour.loc[
        station_hour["Ridership"] < station_hour["Lower Bound"],
        "Anomaly Type",
    ] = "Unusually Low"

    station_hour.loc[
        station_hour["Ridership"] > station_hour["Upper Bound"],
        "Anomaly Type",
    ] = "Unusually High"

    anomalies = station_hour.loc[
        station_hour["Anomaly Type"] != "Normal"
    ].copy()

    anomalies = anomalies.sort_values(
        "Ridership", ascending=False
    ).head(limit)

    records = anomalies[
        [
            "Station",
            "Hour",
            "Ridership",
            "Anomaly Type",
            "Lower Bound",
            "Upper Bound",
        ]
    ].copy()

    for column in ["Lower Bound", "Upper Bound"]:
        records[column] = records[column].round(2)

    return {
        "method": "station-specific_interquartile_range",
        "analysis_granularity": (
            "aggregated historical ridership by station and hour"
        ),
        "anomaly_count": int(
            (station_hour["Anomaly Type"] != "Normal").sum()
        ),
        "returned_count": int(len(records)),
        "anomalies": records.to_dict(orient="records"),
        "interpretation_note": (
            "These are statistical outliers in aggregated hourly "
            "patterns, not confirmed incidents or real-time alerts."
        ),
    }


# ---------------------------------------------------------
# STATION COMPARISON AND PASSENGER FLOW
# ---------------------------------------------------------

def get_station_comparison(limit=20):
    """Return stations ranked by recorded ridership totals."""
    if not 1 <= limit <= 100:
        raise ValueError("limit must be between 1 and 100.")

    records = get_station_ridership()

    return {
        "stations": records[:limit],
        "total_stations": len(records),
        "ranking_basis": "total recorded historical ridership",
    }


def get_network_passenger_flow():
    """Return historical station entry, exit, and net-flow totals."""
    flow = get_station_flow()

    return {
        "station_count": len(flow),
        "stations": flow,
        "data_source": "historical_entry_exit_csv",
        "interpretation_note": (
            "Net flow is calculated as recorded entries minus "
            "recorded exits over the available historical period."
        ),
    }


# ---------------------------------------------------------
# HISTORICAL HOTSPOTS
# ---------------------------------------------------------

def get_analytics_hotspots(limit=20):
    """Return the highest-total station-hour combinations."""
    if not 1 <= limit <= 100:
        raise ValueError("limit must be between 1 and 100.")

    return {
        "hotspots": get_station_hour_hotspots(limit=limit),
        "ranking_basis": (
            "aggregated ridership by station and hour across "
            "the available historical dates"
        ),
    }


# ---------------------------------------------------------
# DATA-DRIVEN MODEL INSIGHTS
# ---------------------------------------------------------

def get_analytics_model_insights():
    """
    Return saved-model metadata, recorded evaluation metrics,
    and feature importance for the existing XGBoost models.

    Crowd-model metrics are notebook-reported results. They are
    not independently reproduced by this API endpoint.
    """
    from app.services.demand_forecasting_service import (
        load_demand_model,
    )
    from app.services.prediction_service import load_prediction_model

    df = _load_analytics_data()

    # Load existing artifacts. Do not retrain models here.
    crowd_model, _ = load_prediction_model()
    demand_model, demand_feature_names = load_demand_model()

    crowd_metrics = {
        "mae": 45.53,
        "rmse": 84.36,
        "r_squared": 0.9691,
        "baseline_mae": 121.23,
        "baseline_rmse": 227.82,
        "baseline_r_squared": 0.7745,
        "mae_improvement_percent": 62.44,
        "rmse_improvement_percent": 62.97,
    }

    demand_metrics = {
        "mae": 75797.70,
        "rmse": 109753.18,
        "r_squared": 0.5361,
        "baseline_mae": 125736.52,
        "baseline_rmse": 175132.80,
        "baseline_r_squared": -0.1812,
        "mae_improvement_percent": 39.72,
    }

    return {
        "available_prediction_model": "XGBoost crowd prediction",
        "prediction_target": "next-hour station ridership estimate",
        "historical_station_count": int(df["Station"].nunique()),
        "historical_start_date": (
            df["Date"].min().strftime("%Y-%m-%d")
            if not df.empty else None
        ),
        "historical_end_date": (
            df["Date"].max().strftime("%Y-%m-%d")
            if not df.empty else None
        ),

        # Required by the AI Predictions frontend.
        "evaluation_metrics": crowd_metrics,
        "evaluation_status": "notebook_evaluated",
        "evaluation_note": (
            "Crowd-model metrics are reported from the notebook's "
            "held-out test evaluation using corrected_xgb_model. "
            "MAE, RMSE, and R-squared have not been independently "
            "reproduced by this API endpoint."
        ),

        "feature_importance": _get_feature_importance(crowd_model),
        "feature_importance_note": (
            "Feature importance describes the fitted model's predictive "
            "patterns and does not establish causation."
        ),

        "demand_model": {
            "model_name": type(demand_model).__name__,
            "feature_count": len(demand_feature_names),
            "evaluation_metrics": demand_metrics,
            "evaluation_status": "saved_artifact_evaluation_reproduced",
            "training_rows": 276,
            "test_rows": 69,
            "test_start_date": "2026-05-01",
            "test_end_date": "2026-09-08",
            "absolute_error_statistics": {
                "median": 38545.75,
                "percentile_90": 201104.59,
                "percentile_95": 246054.01,
            },
            "feature_importance": _get_feature_importance(demand_model),
            "feature_importance_note": (
                "Importance values describe the fitted model, not causal "
                "influence. Absolute-error percentiles summarize the "
                "held-out test set; they are not guaranteed prediction bounds."
            ),
            "data_source": "historical_daily_ridership_csv",
        },

        "data_source": "historical_csv",
    }


# ---------------------------------------------------------
# HISTORICAL STATION-HOUR HEATMAP
# ---------------------------------------------------------

def get_analytics_heatmap():
    """
    Return historical ridership aggregated by station and hour.
    Values represent recorded ridership, not live crowd levels.
    """
    df = _load_analytics_data()

    if df.empty:
        return {
            "stations": [],
            "hours": list(range(24)),
            "heatmap": [],
            "data_source": "historical_csv",
            "interpretation_note": (
                "No historical station-hour ridership data is available."
            ),
        }

    aggregated = (
        df.groupby(["Station", "Hour"], as_index=False)["Ridership"]
        .sum()
    )

    pivot = aggregated.pivot(
        index="Station",
        columns="Hour",
        values="Ridership",
    ).reindex(columns=range(24), fill_value=0).fillna(0)

    pivot = pivot.sort_index()

    heatmap = []

    for station, values in pivot.iterrows():
        heatmap.append({
            "station": str(station),
            "hourly_ridership": [
                int(round(float(value))) for value in values.tolist()
            ],
            "total_ridership": int(round(float(values.sum()))),
        })

    return {
        "stations": pivot.index.tolist(),
        "hours": list(range(24)),
        "heatmap": heatmap,
        "station_count": int(len(pivot)),
        "data_source": "historical_csv",
        "aggregation": (
            "sum of recorded ridership by station and hour "
            "across available historical dates"
        ),
        "interpretation_note": (
            "This heatmap shows historical recorded ridership patterns. "
            "It does not represent live passenger counts, station capacity, "
            "or verified congestion levels."
        ),
    }
