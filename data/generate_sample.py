"""Generate NYC-Subway-style hourly sample dataset (no Kaggle auth needed)
Schema mirrors https://www.kaggle.com/datasets/eddeng/nyc-subway-traffic-data-20172021:
  station_code, timestamp, entries, exits

Also includes download helper for the REAL dataset.
Run: python generate_sample.py --stations 12 --days 90
"""
import argparse
import numpy as np
import pandas as pd
from pathlib import Path

STATIONS = [
    "Times_Sq_42St", "Grand_Central_42St", "Herald_Sq_34St", "Union_Sq_14St",
    "Fulton_St", "Atlantic_Av_Barclays", "Jackson_Hts_Roosevelt", "Flushing_MainSt",
    "125St_Lexington", "Columbus_Circle_59St", "Canal_St", "Brooklyn_Bridge_CityHall",
]

OUT = Path(__file__).parent / "nyc_subway_sample.csv"


def gen_station(code: str, idx: int, days: int, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed + idx * 977)
    hours = pd.date_range("2021-01-01", periods=days * 24, freq="h")
    base = 900 + idx * 160 + rng.normal(0, 40)
    entries = []
    for ts in hours:
        h, dow = ts.hour, ts.dayofweek
        # bimodal peak: 8am & 6pm
        peak = 2.6 * np.exp(-((h - 8) ** 2) / 4.5) + 2.9 * np.exp(-((h - 18) ** 2) / 5.0)
        midday = 0.7 if 10 <= h <= 16 else 0.25
        night = 0.06 if (h <= 4 or h >= 23) else 0.0
        weekend = 0.55 if dow >= 5 else 1.0
        monthly = 1 + 0.08 * np.sin(2 * np.pi * ts.dayofyear / 365)
        noise = rng.normal(1.0, 0.14)
        val = max(0, base * (0.18 + peak + midday - night) * weekend * monthly * noise)
        entries.append(int(val))
    exits = [int(e * rng.normal(0.92, 0.08)) for e in entries]
    return pd.DataFrame({"station_code": code, "timestamp": hours, "entries": entries, "exits": exits})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stations", type=int, default=12)
    ap.add_argument("--days", type=int, default=90)
    ap.add_argument("--out", type=str, default=str(OUT))
    a = ap.parse_args()
    codes = STATIONS[:a.stations]
    df = pd.concat([gen_station(c, i, a.days) for i, c in enumerate(codes)], ignore_index=True)
    df.to_csv(a.out, index=False)
    print(f"Wrote {len(df)} rows x {len(codes)} stations -> {a.out}")
    print(df.head(3).to_string(index=False))
    print(f"Peak-hour avg (8am): {df[pd.to_datetime(df['timestamp']).dt.hour==8]['entries'].mean():.0f} pax/hr")


if __name__ == "__main__":
    main()
