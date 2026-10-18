import pandas as pd
from datetime import datetime
from app.datasets.importers.base_importer import BaseTransitImporter


class SeoulMetroImporter(BaseTransitImporter):
    def parse_and_normalize(self, filepath: str) -> pd.DataFrame:
        df_raw = pd.read_csv(filepath)

        records = []
        for _, row in df_raw.iterrows():
            date_str = str(row["Date"])
            hour = int(row["Hour"])
            dt = datetime.strptime(date_str, "%Y-%m-%d").replace(hour=hour, minute=0)

            inflow_ppm = max(5, int(row["Boarding_Count"] / 60))
            outflow_ppm = max(5, int(row["Alighting_Count"] / 60))
            capacity = 3200 if row["Station_Name"] in ["Gangnam", "Seoul Station"] else 2000

            net_occ = max(40, int((inflow_ppm - outflow_ppm) * 12 + capacity * 0.4))
            density = round(min(99.0, max(5.0, (net_occ / capacity) * 100.0)), 1)

            st_id = 9 if row["Station_Name"] == "Seoul Station" else 10

            records.append({
                "timestamp": dt.strftime("%Y-%m-%d %H:%M:%S"),
                "station_id": st_id,
                "station_code": f"SEOUL-0{st_id}",
                "station_name": f"Seoul Metro - {row['Station_Name']}",
                "line_name": row["Line_Name"],
                "hour": dt.hour,
                "minute": dt.minute,
                "day_of_week": dt.weekday(),
                "is_weekend": int(dt.weekday() >= 5),
                "capacity": capacity,
                "inflow_ppm": inflow_ppm,
                "outflow_ppm": outflow_ppm,
                "line_delay_min": 0,
                "density_pct": density,
            })

        return pd.DataFrame(records)
