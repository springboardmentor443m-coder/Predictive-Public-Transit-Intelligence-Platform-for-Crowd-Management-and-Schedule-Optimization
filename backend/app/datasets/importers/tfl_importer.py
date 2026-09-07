import json
import pandas as pd
from datetime import datetime
from app.datasets.importers.base_importer import BaseTransitImporter


class TfLImporter(BaseTransitImporter):
    def parse_and_normalize(self, filepath: str) -> pd.DataFrame:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        records = []
        for item in data:
            dt = datetime.strptime(item["timestamp"], "%Y-%m-%dT%H:%M:%SZ")
            inflow_ppm = max(5, int(item["taps_in"] / 15))
            outflow_ppm = max(5, int(item["taps_out"] / 15))
            capacity = 2800

            net_occ = max(35, int((inflow_ppm - outflow_ppm) * 10 + capacity * 0.38))
            density = round(min(99.0, max(5.0, (net_occ / capacity) * 100.0)), 1)

            records.append({
                "timestamp": dt.strftime("%Y-%m-%d %H:%M:%S"),
                "station_id": 11,
                "station_code": "TFL-01",
                "station_name": f"TfL Underground - {item['station']}",
                "line_name": item["line"],
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
