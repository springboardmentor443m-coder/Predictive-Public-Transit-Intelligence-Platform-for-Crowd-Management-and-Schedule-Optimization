import pandas as pd
import os

SCHEDULE_FILE = os.path.join("data", "active_schedules.csv")
OUTPUT_FILE = os.path.join("data", "frequency_recommendations.csv")

def calculate_frequency_adjustments():
    if not os.path.exists(SCHEDULE_FILE):
        print("Error: active_schedules.csv missing.")
        return

    df = pd.read_csv(SCHEDULE_FILE)

    def determine_adjustment(row):
        delay = float(row.get("delay_minutes", 0.0))
        occ = float(row.get("occupancy_rate", 0.0))
        base_headway = int(row.get("scheduled_headway_min", 8))

        # Dynamic Headway Compression Logic
        if delay >= 5.0 or occ >= 0.85:
            rec_headway = 3
            action = "DISPATCH EXTRA TRAIN"
            reason = "Severe delay / Platform saturation risk"
        elif delay >= 2.0 or occ >= 0.65:
            rec_headway = 5
            action = "INCREASE FREQUENCY"
            reason = "Moderate corridor congestion"
        else:
            rec_headway = base_headway
            action = "MAINTAIN HEADWAY"
            reason = "Nominal operating flow"

        headway_delta = base_headway - rec_headway

        return pd.Series([base_headway, rec_headway, headway_delta, action, reason])

    cols = ["current_headway_min", "adjusted_headway_min", "headway_saved_min", "recommended_action", "trigger_reason"]
    df[cols] = df.apply(determine_adjustment, axis=1)

    df.to_csv(OUTPUT_FILE, index=False)
    print(f"Step 7 Complete: Frequency adjustments written to {OUTPUT_FILE}")

if __name__ == "__main__":
    calculate_frequency_adjustments()