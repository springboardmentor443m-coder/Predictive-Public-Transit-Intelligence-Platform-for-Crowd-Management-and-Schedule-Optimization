import pandas as pd
from pathlib import Path


DATASET_PATH = Path("datasets/raw/station-hourly.csv")


def main():
    print("Loading dataset...")

    df = pd.read_csv(
        DATASET_PATH,
        sep=";"
    )

    print("\n========== BASIC INFORMATION ==========")
    print(f"Rows: {len(df):,}")
    print(f"Columns: {len(df.columns)}")
    print(f"Column names: {list(df.columns)}")

    print("\n========== FIRST 10 ROWS ==========")
    print(df.head(10).to_string(index=False))

    print("\n========== DATA TYPES ==========")
    print(df.dtypes)

    print("\n========== MISSING VALUES ==========")
    print(df.isnull().sum())

    print("\n========== DUPLICATE ROWS ==========")
    print(f"Duplicates: {df.duplicated().sum():,}")

    print("\n========== DATE RANGE ==========")
    print(f"Start date: {df['Date'].min()}")
    print(f"End date:   {df['Date'].max()}")

    print("\n========== STATION INFORMATION ==========")
    print(f"Number of stations: {df['Station'].nunique():,}")

    print("\nStation names:")
    for station in sorted(df["Station"].dropna().unique()):
        print(f" - {station}")

    print("\n========== HOUR INFORMATION ==========")
    print(f"Minimum hour: {df['Hour'].min()}")
    print(f"Maximum hour: {df['Hour'].max()}")

    print("\n========== RIDERSHIP STATISTICS ==========")
    print(df["Ridership"].describe())

    print("\n========== TOP 10 HIGHEST RIDERSHIP RECORDS ==========")
    print(
        df.nlargest(10, "Ridership")[
            ["Date", "Hour", "Station", "Ridership"]
        ].to_string(index=False)
    )

    print("\n========== AVERAGE RIDERSHIP BY HOUR ==========")
    hourly = (
        df.groupby("Hour")["Ridership"]
        .mean()
        .sort_values(ascending=False)
    )
    print(hourly.to_string())

    print("\n========== AVERAGE RIDERSHIP BY STATION ==========")
    station_avg = (
        df.groupby("Station")["Ridership"]
        .mean()
        .sort_values(ascending=False)
    )
    print(station_avg.to_string())


if __name__ == "__main__":
    main()