import pandas as pd
from datetime import datetime
from app.datasets.importers.base_importer import BaseTransitImporter


class MTADataImporter(BaseTransitImporter):
    def parse_and_normalize(self, filepath: str) -> pd.DataFrame:
        df_raw = pd.read_csv(filepath)
        df_raw.columns = [c.strip() for c in df_raw.columns]

        records = []
        # Sort by turnstile unit, SCP, and datetime
        df_raw["dt"] = pd.to_datetime(df_raw["DATE"] + " " + df_raw["TIME"], format="%m/%d/%Y %H:%M:%S")
        df_raw = df_raw.sort_values(by=["C/A", "UNIT", "SCP", "STATION", "dt"])

        # Group by station and calculate differences in cumulative ENTRIES / EXITS
        for (station, line), group in df_raw.groupby(["STATION", "LINENAME"]):
            group = group.copy()
            group["inflow"] = group["ENTRIES"].diff().fillna(25).clip(lower=0, upper=3000)
            group["outflow"] = group["EXITS"].diff().fillna(20).clip(lower=0, upper=3000)

            for _, row in group.iterrows():
                dt = row["dt"]
                inflow_ppm = max(5, int(row["inflow"] / 240))  # Convert 4-hr block to ppm
                outflow_ppm = max(5, int(row["outflow"] / 240))
                capacity = 3000 if "GRD CNTRL" in station else 2200

                net_occ = max(30, int((inflow_ppm - outflow_ppm) * 15 + capacity * 0.35))
                density = round(min(99.0, max(5.0, (net_occ / capacity) * 100.0)), 1)

                records.append({
                    "timestamp": dt.strftime("%Y-%m-%d %H:%M:%S"),
                    "station_id": 1 if "GRD CNTRL" in station else 2,
                    "station_code": "MTA-01" if "GRD CNTRL" in station else "MTA-02",
                    "station_name": f"NYC MTA - {station.title()}",
                    "line_name": "NYC Subway Line",
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
