from pathlib import Path
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

print("--- 1. SEOUL METRO STATION INFO COLUMNS ---")
df_st = pd.read_csv(DATA_DIR / "seoul-metro-station-info.csv", nrows=3)
print(df_st.columns.tolist())
print(df_st.head(2))

print("\n--- 2. SEOUL METRO 2021 LOGS SAMPLE ---")
df_logs = pd.read_csv(DATA_DIR / "seoul-metro-2021.logs.csv", nrows=3)
print(df_logs.columns.tolist())
print(df_logs.head(2))

print("\n--- 3. DELHI METRO COLUMNS ---")
if (DATA_DIR / "delhi_metro_updated.csv").exists():
    df_delhi = pd.read_csv(DATA_DIR / "delhi_metro_updated.csv", nrows=3)
    print(df_delhi.columns.tolist())
    print(df_delhi.head(2))