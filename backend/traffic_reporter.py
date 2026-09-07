import pandas as pd
import json
import os

PATTERNS_FILE = os.path.join("data", "traffic_patterns.csv")
FREQ_FILE = os.path.join("data", "frequency_recommendations.csv")
PEAK_FILE = os.path.join("data", "peak_hour_policy.csv")
REPORT_FILE = os.path.join("data", "traffic_analysis_report.json")

def generate_traffic_report():
    report = {
        "report_title": "MetroFlow Network Congestion & Operations Summary",
        "generated_at": "2026-09-05T19:00:00Z",
        "system_kpis": {},
        "bottleneck_hotspots": [],
        "fleet_dispatch_directives": [],
        "peak_window_profiles": []
    }

    # 1. Analyze Traffic Patterns
    if os.path.exists(PATTERNS_FILE):
        pdf = pd.read_csv(PATTERNS_FILE)
        bottlenecks = pdf[pdf["bottleneck_profile"] == "CHRONIC BOTTLENECK"]
        report["bottleneck_hotspots"] = bottlenecks[["station_id", "time_segment", "avg_inflow", "flow_volatility"]].to_dict(orient="records")
        report["system_kpis"]["chronic_bottlenecks_count"] = int(len(bottlenecks))
        report["system_kpis"]["highest_station_surge"] = int(pdf["peak_inflow"].max())

    # 2. Analyze Scheduling & Fleet Adjustments
    if os.path.exists(FREQ_FILE):
        fdf = pd.read_csv(FREQ_FILE)
        extra_trains = fdf[fdf["recommended_action"].str.contains("DISPATCH", na=False)]
        report["fleet_dispatch_directives"] = extra_trains[["route_id", "current_headway_min", "adjusted_headway_min", "recommended_action"]].to_dict(orient="records")
        report["system_kpis"]["extra_train_deployments_needed"] = int(len(extra_trains))
        report["system_kpis"]["avg_headway_reduction_min"] = round(float(fdf["headway_saved_min"].mean()), 1)

    # 3. Analyze Peak Hour Policies
    if os.path.exists(PEAK_FILE):
        pkdf = pd.read_csv(PEAK_FILE)
        surges = pkdf[pkdf["congestion_risk"].isin(["SURGE DEMAND", "CRITICAL SURGE"])].drop_duplicates(subset=["time_window"])
        report["peak_window_profiles"] = surges[["time_window", "target_passenger_capacity", "fleet_strategy"]].to_dict(orient="records")

    with open(REPORT_FILE, "w") as f:
        json.dump(report, f, indent=2)

    print(f"Step 11 Complete: Traffic report generated at {REPORT_FILE}")

if __name__ == "__main__":
    generate_traffic_report()
    