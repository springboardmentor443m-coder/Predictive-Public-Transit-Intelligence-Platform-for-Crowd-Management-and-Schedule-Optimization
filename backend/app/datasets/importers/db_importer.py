import pandas as pd
from datetime import datetime
from app.datasets.importers.base_importer import BaseTransitImporter


class DeutscheBahnImporter(BaseTransitImporter):
    def parse_and_normalize(self, filepath: str) -> pd.DataFrame:
        df_raw = pd.read_csv(filepath)

        records = []
        for _, row in df_raw.iterrows():
            date_str = str(row["Date"])
            sched_time = str(row["Scheduled_Time"])
            dt = datetime.strptime(f"{date_str} {sched_time}", "%Y-%m-%d %H:%M:%S")

            delay = int(row["Delay_Minutes"])
            inflow_ppm = random_inflow = 65
            outflow_ppm = 55
            capacity = 2500

            # Higher delay creates artificial crowd backlog density spike
            density_boost = delay * 1.5
            density = round(min(99.0, max(15.0, 50.0 + density_boost)), 1)

            records.append({
                "timestamp": dt.strftime("%Y-%m-%d %H:%M:%S"),
                "station_id": 12,
                "station_code": "DB-01",
                "station_name": f"Deutsche Bahn - {row['Station']}",
                "line_name": f"DB Corridor ({row['Train_ID']})",
                "hour": dt.hour,
                "minute": dt.minute,
                "day_of_week": dt.weekday(),
                "is_weekend": int(dt.weekday() >= 5),
                "capacity": capacity,
                "inflow_ppm": inflow_ppm,
                "outflow_ppm": outflow_ppm,
                "line_delay_min": delay,
                "density_pct": density,
            })

        return pd.DataFrame(records)
