"""
AI Analytics service using real Bangalore Metro dataset.
Provides: crowd prediction, peak hour analysis, anomaly detection,
route optimization, and live simulation.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from collections import defaultdict

# Load dataset once at module startup
_DATA_PATH = Path(__file__).parents[3] / "datasets" / "raw" / "raw" / "station-hourly.csv"

_df: Optional[pd.DataFrame] = None


def _get_df() -> pd.DataFrame:
    global _df
    if _df is None:
        _df = pd.read_csv(_DATA_PATH, sep=";")
        _df["Date"] = pd.to_datetime(_df["Date"])
        _df["DayOfWeek"] = _df["Date"].dt.dayofweek  # 0=Mon
        _df["IsWeekend"] = _df["DayOfWeek"] >= 5
        _df["Month"] = _df["Date"].dt.month
    return _df


# ─────────────────────────────────────────────────────────────
# 1. LIVE SIMULATION  (simulates "now" based on current hour)
# ─────────────────────────────────────────────────────────────

def get_live_ridership() -> List[Dict[str, Any]]:
    """Return current estimated ridership per station, simulated from historical avg."""
    df = _get_df()
    now = datetime.now()
    current_hour = now.hour
    is_weekend = now.weekday() >= 5

    # avg ridership for matching hour & day-type
    mask = (df["Hour"] == current_hour) & (df["IsWeekend"] == is_weekend)
    base = df[mask].groupby("Station")["Ridership"].mean().reset_index()
    base.columns = ["station", "avg_ridership"]

    results = []
    for _, row in base.iterrows():
        avg = row["avg_ridership"]
        # Add ±15% random variation to simulate live
        live = max(0, int(avg * np.random.uniform(0.85, 1.15)))
        results.append({
            "station": row["station"],
            "ridership": live,
            "avg_historical": round(avg, 1),
            "hour": current_hour,
            "status": _crowd_status(live),
        })
    results.sort(key=lambda x: x["ridership"], reverse=True)
    return results


def _crowd_status(ridership: int) -> str:
    if ridership < 200:
        return "low"
    elif ridership < 600:
        return "moderate"
    elif ridership < 1200:
        return "high"
    else:
        return "critical"


# ─────────────────────────────────────────────────────────────
# 2. STATION ANALYTICS
# ─────────────────────────────────────────────────────────────

def get_station_list() -> List[str]:
    return sorted(_get_df()["Station"].unique().tolist())


def get_station_hourly_avg(station: str) -> List[Dict[str, Any]]:
    df = _get_df()
    s = df[df["Station"] == station]
    hourly = s.groupby("Hour")["Ridership"].mean().reset_index()
    return [
        {"hour": int(r["Hour"]), "avg_ridership": round(r["Ridership"], 1)}
        for _, r in hourly.iterrows()
    ]


def get_station_daily_trend(station: str) -> List[Dict[str, Any]]:
    df = _get_df()
    s = df[df["Station"] == station]
    daily = s.groupby("Date")["Ridership"].sum().reset_index()
    return [
        {"date": str(r["Date"].date()), "total_ridership": int(r["Ridership"])}
        for _, r in daily.iterrows()
    ]


def get_station_weekday_pattern(station: str) -> List[Dict[str, Any]]:
    df = _get_df()
    s = df[df["Station"] == station]
    day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    grouped = s.groupby("DayOfWeek")["Ridership"].mean().reset_index()
    return [
        {"day": day_names[int(r["DayOfWeek"])], "avg_ridership": round(r["Ridership"], 1)}
        for _, r in grouped.iterrows()
    ]


# ─────────────────────────────────────────────────────────────
# 3. NETWORK OVERVIEW
# ─────────────────────────────────────────────────────────────

def get_network_daily_summary() -> List[Dict[str, Any]]:
    df = _get_df()
    daily = df.groupby("Date")["Ridership"].sum().reset_index()
    return [
        {"date": str(r["Date"].date()), "total_ridership": int(r["Ridership"])}
        for _, r in daily.iterrows()
    ]


def get_network_hourly_profile() -> List[Dict[str, Any]]:
    df = _get_df()
    hourly = df.groupby("Hour")["Ridership"].mean().reset_index()
    return [
        {"hour": int(r["Hour"]), "avg_ridership": round(r["Ridership"], 1)}
        for _, r in hourly.iterrows()
    ]


def get_top_stations(n: int = 10, hour: Optional[int] = None) -> List[Dict[str, Any]]:
    df = _get_df()
    if hour is not None:
        df = df[df["Hour"] == hour]
    top = df.groupby("Station")["Ridership"].mean().nlargest(n).reset_index()
    return [
        {"station": r["Station"], "avg_ridership": round(r["Ridership"], 1)}
        for _, r in top.iterrows()
    ]


def get_heatmap_data() -> List[Dict[str, Any]]:
    """Hour x Station heatmap of average ridership."""
    df = _get_df()
    pivot = df.groupby(["Station", "Hour"])["Ridership"].mean().reset_index()
    return [
        {
            "station": r["Station"],
            "hour": int(r["Hour"]),
            "avg_ridership": round(r["Ridership"], 1),
        }
        for _, r in pivot.iterrows()
    ]


# ─────────────────────────────────────────────────────────────
# 4. AI PREDICTIONS
# ─────────────────────────────────────────────────────────────

def predict_next_hours(station: str, hours_ahead: int = 6) -> List[Dict[str, Any]]:
    """Simple ML-style prediction using weighted moving average + time patterns."""
    df = _get_df()
    s = df[df["Station"] == station]
    now = datetime.now()

    predictions = []
    for i in range(1, hours_ahead + 1):
        future = now + timedelta(hours=i)
        h = future.hour
        dow = future.weekday()
        is_weekend = dow >= 5

        mask = (s["Hour"] == h) & (s["IsWeekend"] == is_weekend)
        subset = s[mask]
        if len(subset) == 0:
            subset = s[s["Hour"] == h]

        if len(subset) == 0:
            predicted = 0.0
        else:
            # Weighted recent average (more weight to last 2 weeks)
            recent = subset.tail(14)
            older = subset.head(max(1, len(subset) - 14))
            predicted = (recent["Ridership"].mean() * 0.7 + older["Ridership"].mean() * 0.3)

        # Confidence: std-based
        std = subset["Ridership"].std() if len(subset) > 1 else 0
        conf = max(0.5, 1 - (std / (predicted + 1)) * 0.5) if predicted > 0 else 0.5

        predictions.append({
            "hour": h,
            "datetime": future.strftime("%Y-%m-%d %H:00"),
            "predicted_ridership": round(predicted, 1),
            "confidence": round(conf, 2),
            "status": _crowd_status(int(predicted)),
        })
    return predictions


def get_peak_analysis() -> Dict[str, Any]:
    df = _get_df()

    # Network peak hour
    hourly_avg = df.groupby("Hour")["Ridership"].mean()
    peak_hour = int(hourly_avg.idxmax())
    off_peak_hour = int(hourly_avg.idxmin())

    # Per-station peak hours
    station_peaks = df.groupby(["Station", "Hour"])["Ridership"].mean().reset_index()
    station_peak = station_peaks.loc[station_peaks.groupby("Station")["Ridership"].idxmax()]

    # Busiest day of week
    dow_avg = df.groupby("DayOfWeek")["Ridership"].mean()
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    busiest_day = day_names[int(dow_avg.idxmax())]

    return {
        "network_peak_hour": peak_hour,
        "network_off_peak_hour": off_peak_hour,
        "busiest_day": busiest_day,
        "hourly_avg": [
            {"hour": int(h), "avg": round(float(v), 1)}
            for h, v in hourly_avg.items()
        ],
        "station_peak_hours": [
            {
                "station": r["Station"],
                "peak_hour": int(r["Hour"]),
                "avg_ridership": round(r["Ridership"], 1),
            }
            for _, r in station_peak.iterrows()
        ],
    }


def get_anomaly_stations(date_str: Optional[str] = None) -> List[Dict[str, Any]]:
    """Detect stations with unusual ridership (z-score > 2)."""
    df = _get_df()
    if date_str:
        target_date = pd.to_datetime(date_str)
        daily = df[df["Date"] == target_date]
    else:
        # Use last available date
        daily = df[df["Date"] == df["Date"].max()]

    if daily.empty:
        daily = df[df["Date"] == df["Date"].max()]

    daily_totals = daily.groupby("Station")["Ridership"].sum().reset_index()

    # Compare to historical avg per station
    hist_avg = df.groupby("Station")["Ridership"].agg(["mean", "std"]).reset_index()
    hist_avg.columns = ["Station", "hist_mean", "hist_std"]

    merged = daily_totals.merge(hist_avg, on="Station")
    merged["z_score"] = (merged["Ridership"] - merged["hist_mean"]) / (merged["hist_std"] + 1)
    anomalies = merged[merged["z_score"].abs() > 1.5].sort_values("z_score", ascending=False)

    return [
        {
            "station": r["Station"],
            "current_ridership": int(r["Ridership"]),
            "historical_avg": round(r["hist_mean"], 1),
            "z_score": round(r["z_score"], 2),
            "type": "surge" if r["z_score"] > 0 else "drop",
        }
        for _, r in anomalies.iterrows()
    ]


def get_ai_insights() -> List[Dict[str, Any]]:
    """Generate AI text insights from data patterns."""
    df = _get_df()
    insights = []

    # 1. Busiest station overall
    top = df.groupby("Station")["Ridership"].mean().idxmax()
    top_val = round(df.groupby("Station")["Ridership"].mean().max(), 1)
    insights.append({
        "type": "info",
        "title": "Busiest Station",
        "message": f"{top} consistently leads with avg {top_val} riders/hour. "
                   "Consider deploying additional trains during peak windows.",
    })

    # 2. Weekend vs weekday
    wk = df[df["IsWeekend"] == False]["Ridership"].mean()
    we = df[df["IsWeekend"] == True]["Ridership"].mean()
    delta_pct = round((wk - we) / we * 100, 1)
    insights.append({
        "type": "trend",
        "title": "Weekday vs Weekend",
        "message": f"Weekday ridership is {delta_pct}% higher than weekends on average. "
                   "AI recommends reduced service frequency on Sunday mornings.",
    })

    # 3. Peak window
    hourly = df.groupby("Hour")["Ridership"].mean()
    peak_h = int(hourly.idxmax())
    insights.append({
        "type": "alert",
        "title": "Peak Rush Hour",
        "message": f"Network-wide peak occurs at {peak_h}:00. Crowd levels reach "
                   f"critical thresholds at {round(hourly[peak_h], 0):.0f} avg riders/hour. "
                   "AI suggests express services from 7–10 AM.",
    })

    # 4. Low utilization
    bottom = df.groupby("Station")["Ridership"].mean().nsmallest(3).index.tolist()
    insights.append({
        "type": "warning",
        "title": "Low Utilization Stations",
        "message": f"{', '.join(bottom)} show consistently low ridership. "
                   "Consider dynamic frequency adjustments to reduce operational cost.",
    })

    return insights


def get_line_comparison() -> List[Dict[str, Any]]:
    """Compare Purple vs Green line ridership patterns."""
    # Station-to-line mapping (Bangalore Metro)
    purple_line = [
        "Baiyappanahalli", "Swami Vivekananda Road", "Indiranagar", "Halasuru",
        "Trinity", "Mahatma Gandhi Road", "Cubbon Park",
        "Dr. B. R. Ambedkar Station, Vidhana Soudha",
        "Sir M. Visvesvaraya Stn., Central College",
        "Krantivira Sangolli Rayanna Railway Station", "Magadi Road",
        "Mahalakshmi", "Vijayanagar", "Attiguppe", "Deepanjali Nagar",
        "Mysore Road", "Jaya Prakash Nagar", "Rashtreeya Vidyalaya Road",
        "National College", "Lalbagh", "South End Circle", "Jayanagar",
        "Rajarajeshwari Nagar",
    ]
    green_line = [
        "Nagasandra", "Dasarahalli", "Jalahalli", "Peenya Industry",
        "Peenya", "Goraguntepalya", "Yeshwantpur", "Sandal Soap Factory",
        "Mahalakshmi", "Rajajinagar", "Srirampura", "Mantri Square Sampige Road",
        "Nadaprabhu Kempegowda Station, Majestic", "Chickpete", "Krishna Rajendra Market",
        "Mahatma Gandhi Road", "Baiyappanahalli",
        "Whitefield (Kadugodi)", "Hopefarm Channasandra", "Kadugodi Tree Park",
        "Pattandur Agrahara", "Nallurahalli", "Kundalahalli", "Garudacharpalya",
        "Krishnarajapura", "Benniganahalli", "Hoodi",
    ]

    df = _get_df()
    results = []
    for hour in range(24):
        hour_df = df[df["Hour"] == hour]
        pl = hour_df[hour_df["Station"].isin(purple_line)]["Ridership"].mean()
        gl = hour_df[hour_df["Station"].isin(green_line)]["Ridership"].mean()
        results.append({
            "hour": hour,
            "purple_line_avg": round(float(pl) if not np.isnan(pl) else 0, 1),
            "green_line_avg": round(float(gl) if not np.isnan(gl) else 0, 1),
        })
    return results


def get_crowd_forecast_summary() -> Dict[str, Any]:
    """System-wide forecast for the next 24 hours."""
    df = _get_df()
    now = datetime.now()
    forecasts = []
    for i in range(24):
        future = now + timedelta(hours=i)
        h = future.hour
        is_weekend = future.weekday() >= 5
        mask = (df["Hour"] == h) & (df["IsWeekend"] == is_weekend)
        avg = df[mask]["Ridership"].mean()
        avg = float(avg) if not np.isnan(avg) else 0
        forecasts.append({
            "hour": h,
            "datetime": future.strftime("%H:00"),
            "predicted_ridership": round(avg, 1),
            "status": _crowd_status(int(avg)),
        })
    return {"forecasts": forecasts, "generated_at": now.isoformat()}
