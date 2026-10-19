
from pathlib import Path
import json
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data" / "bmrcl"
OUTPUT_DIR = DATA_DIR / "demo_2026"

FILES = ["station-hourly.csv", "station-hourly-exits.csv"]

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

metadata = {
    "dataset_type": "SIMULATED DEMONSTRATION DATA",
    "simulation_method": (
        "Dates shifted to 2026; passenger counts remain historical "
        "and are not actual 2026 observations."
    ),
    "is_live_data": False,
    "is_observed_2026_data": False,
    "original_files_preserved": True,
}

for filename in FILES:
    source = DATA_DIR / filename

    if not source.exists():
        raise FileNotFoundError(f"Source dataset not found: {source}")

    df = pd.read_csv(source, sep=";")

    if "Date" not in df.columns:
        raise ValueError(f"Date column missing from {filename}")

    dates = pd.to_datetime(df["Date"], errors="raise")

    if ((dates.dt.month == 2) & (dates.dt.day == 29)).any():
        raise ValueError(f"February 29 found in {filename}; handle separately.")

    df["Date"] = dates.map(
        lambda d: d.replace(year=2026).strftime("%Y-%m-%d")
    )

    output = OUTPUT_DIR / filename
    df.to_csv(output, sep=";", index=False)

    print(f"Created: {output}")
    print(f"Rows: {len(df):,}")
    print(f"Date range: {df['Date'].min()} to {df['Date'].max()}")

(OUTPUT_DIR / "DEMO_DATA_METADATA.json").write_text(
    json.dumps(metadata, indent=2),
    encoding="utf-8",
)

print("\nDemo datasets created. These are NOT live observations.")
