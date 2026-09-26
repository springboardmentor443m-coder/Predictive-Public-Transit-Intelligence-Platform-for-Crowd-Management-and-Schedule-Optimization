import pandas as pd


DATA_PATH = "../data/bmrcl/station-hourly.csv"


def load_ridership_data():
    df = pd.read_csv(
        DATA_PATH,
        sep=";"
    )

    df["Date"] = pd.to_datetime(df["Date"])

    return df


def get_station_ridership():
    df = load_ridership_data()

    station_data = (
        df.groupby("Station")["Ridership"]
        .sum()
        .reset_index()
        .sort_values(
            "Ridership",
            ascending=False
        )
    )

    return station_data.to_dict(
        orient="records"
    )

def get_hourly_ridership():
    df = load_ridership_data()

    hourly_data = (
        df.groupby("Hour")["Ridership"]
        .sum()
        .reset_index()
        .sort_values(
            "Hour"
        )
    )

    return hourly_data.to_dict(
        orient="records"
    )