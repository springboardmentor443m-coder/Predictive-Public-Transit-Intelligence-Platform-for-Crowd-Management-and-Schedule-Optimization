"""Dataset loader: supports real NYC Subway Traffic CSV or bundled sample."""
from pathlib import Path
import pandas as pd

EXPECTED_COLS = {"station", "station_code", "timestamp", "datetime", "entries", "exits"}


def find_data_file(configured: str) -> Path | None:
    candidates = [
        Path(configured),
        Path(__file__).resolve().parents[3] / "data" / "nyc_subway_sample.csv",
        Path("data/nyc_subway_sample.csv"),
        Path("../data/nyc_subway_sample.csv"),
    ]
    # Also accept full Kaggle download name variants
    for p in list(candidates):
        if p.exists():
            return p
    data_dir = Path(__file__).resolve().parents[3] / "data"
    if data_dir.exists():
        for f in data_dir.glob("*.csv"):
            return f
    return None


def load_ridership_df(configured: str) -> pd.DataFrame:
    path = find_data_file(configured)
    if path is None:
        raise FileNotFoundError("No ridership CSV found in data/. Run data/generate_sample.py first.")
    df = pd.read_csv(path)
    # Normalize column names (Kaggle NYC file uses various casings)
    df.columns = [c.strip().lower() for c in df.columns]
    rename = {
        "station_code": "station_code", "stationcode": "station_code",
        "station": "station_code", "station_name": "station_code",
        "datetime": "timestamp", "date_time": "timestamp", "transit_timestamp": "timestamp",
        "timestamp": "timestamp", "date": "timestamp", "hour": "hour_col",
        "ridership": "entries", "entries": "entries", "boardings": "entries",
        "exits": "exits", "alightings": "exits",
    }
    for k, v in rename.items():
        if k in df.columns and v not in df.columns:
            df = df.rename(columns={k: v})
    if "timestamp" not in df.columns:
        # Try compose from date+hour
        if "date" in df.columns:
            df["timestamp"] = pd.to_datetime(df["date"])
        else:
            raise ValueError(f"CSV missing timestamp column. Found: {list(df.columns)}")
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    if "station_code" not in df.columns:
        df["station_code"] = "ST-001"
    for c in ("entries", "exits"):
        if c not in df.columns:
            df[c] = 0
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype(int)
    df["station_code"] = df["station_code"].astype(str)
    return df[["station_code", "timestamp", "entries", "exits"]].sort_values(
        ["station_code", "timestamp"]
    ).reset_index(drop=True)
