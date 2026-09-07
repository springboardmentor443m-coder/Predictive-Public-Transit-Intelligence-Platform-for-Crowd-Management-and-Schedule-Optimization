"""Central configuration for MetroFlow data paths.

Paths are resolved relative to the project root so the project can be
cloned/moved without hardcoded machine-specific paths.

This milestone covers: project setup, data ingestion & profiling, and
feature engineering. Later milestones (model training, congestion,
scheduling, alerts, analytics, database, API, auth, frontend) will extend
this file incrementally in subsequent commits.
"""
from pathlib import Path

PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent

# Raw Kaggle dataset (Taipei MRT hourly OD traffic). Must never be modified.
RAW_DATA_DIR: Path = PROJECT_ROOT / "archive"
RAW_DATA_GLOB: str = "*.parquet.gzip"

# Station line/metadata reference files (bundled with the Kaggle dataset).
LINE_METADATA_FILE: Path = RAW_DATA_DIR / "tpe_mrt_lines.json"

# Output locations for generated (non-raw) artifacts.
REPORTS_DIR: Path = PROJECT_ROOT / "reports"
DATA_DICTIONARY_PATH: Path = REPORTS_DIR / "data_dictionary.md"
PROFILE_REPORT_JSON_PATH: Path = REPORTS_DIR / "profiling_report.json"
PROFILE_REPORT_MD_PATH: Path = REPORTS_DIR / "profiling_report.md"

# Feature engineering: engineered/processed data outputs (derived, never raw).
PROCESSED_DATA_DIR: Path = PROJECT_ROOT / "data" / "processed"
STATION_HOURLY_AGG_PATH: Path = PROCESSED_DATA_DIR / "station_hourly_aggregated.parquet"
STATION_HOURLY_FEATURES_PATH: Path = PROCESSED_DATA_DIR / "station_hourly_features.parquet"
FEATURE_ENGINEERING_REPORT_MD_PATH: Path = REPORTS_DIR / "feature_engineering_report.md"

# Raw dataset column names (Chinese, as provided by the source).
COL_DATE = "日期"
COL_HOUR = "時段"
COL_ENTRY_STATION = "進站"
COL_EXIT_STATION = "出站"
COL_TRIP_COUNT = "人次"

RAW_COLUMNS = [COL_DATE, COL_HOUR, COL_ENTRY_STATION, COL_EXIT_STATION, COL_TRIP_COUNT]

# Canonical schema used by the feature-engineering pipeline (and by later
# milestones' modeling/business-logic code, kept stable on purpose).
TARGET_STATION_COL = "station"
TARGET_DATETIME_COL = "datetime"
TARGET_INFLOW_COL = "inflow"
TARGET_OUTFLOW_COL = "outflow"
PREDICTION_HORIZON_HOURS = 1
