import pandas as pd
import os

PATTERNS_FILE = os.path.join("data", "traffic_patterns.csv")
CROWD_FILE = os.path.join("data", "live_crowd_summary.csv")
SCHEDULE_FILE = os.path.join("data", "active_schedules.csv")
OUTPUT_FILE = os.path.join("data", "ai_recommendations.csv")

def generate_recommendations():
    recommendations = []

    # 1. Station Traffic Inflow & Crowding Analysis
    source_df = None
    if os.path.exists(PATTERNS_FILE):
        source_df = pd.read_csv(PATTERNS_FILE)
    elif os.path.exists(CROWD_FILE):
        source_df = pd.read_csv(CROWD_FILE)

    if source_df is not None:
        for _, row in source_df.iterrows():
            stn = row.get('station_id', 'Unknown Station')
            inflow = float(row.get('peak_inflow', row.get('inflow', 0)))
            congestion = str(row.get('congestion_level', row.get('hub_classification', 'NORMAL')))

            if inflow > 2500 or "CRITICAL" in congestion.upper():
                recommendations.append({
                    "target_entity": str(stn),
                    "domain": "STATION_CROWD",
                    "priority": "CRITICAL",
                    "action_required": "Deploy platform crowd marshals; enforce staggered turnstile metering.",
                    "estimated_impact": "Prevents platform overfill; reduces boarding bottleneck by ~30%."
                })
            elif inflow > 1200 or "HIGH" in congestion.upper() or "COMMUTER" in congestion.upper():
                recommendations.append({
                    "target_entity": str(stn),
                    "domain": "STATION_CROWD",
                    "priority": "MEDIUM",
                    "action_required": "Adjust digital wayfinding displays to guide passengers toward trailing cars.",
                    "estimated_impact": "Balances passenger distribution; cuts station dwell time by 15-20s."
                })

    # 2. Rail Line Delays & Headway Optimization
    if os.path.exists(SCHEDULE_FILE):
        sdf = pd.read_csv(SCHEDULE_FILE)
        for _, row in sdf.iterrows():
            route = row.get('route_id', 'Transit Line')
            delay = float(row.get('delay_minutes', 0.0))

            if delay >= 5.0:
                recommendations.append({
                    "target_entity": str(route),
                    "domain": "FLEET_SCHEDULING",
                    "priority": "HIGH",
                    "action_required": f"Inject reserve train at interchange; compress headway from 8m to 3m.",
                    "estimated_impact": f"Absorbs the current {delay} min delay backlog."
                })
            elif delay >= 2.0:
                recommendations.append({
                    "target_entity": str(route),
                    "domain": "FLEET_SCHEDULING",
                    "priority": "LOW",
                    "action_required": "Hold departing train 45s at terminal hub to synchronize timetable.",
                    "estimated_impact": "Stabilizes headway intervals across subsequent stations."
                })

    rec_df = pd.DataFrame(recommendations)
    rec_df.head(15).to_csv(OUTPUT_FILE, index=False)
    print(f"Step 12 Complete: AI Recommendations saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    generate_recommendations()