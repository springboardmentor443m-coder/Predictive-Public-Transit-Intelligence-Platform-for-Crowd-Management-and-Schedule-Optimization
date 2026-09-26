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


def get_daily_ridership():
    df = pd.read_csv(
        "../data/bmrcl/daily-ridership.csv"
    )

    df["Record Date"] = pd.to_datetime(
        df["Record Date"],
        format="%d-%m-%Y"
    )

    df["Total Ridership"] = (
        df["Total Smart Cards"]
        + df["Total Tokens"]
        + df["Total NCMC"]
        + df["Group Ticket"]
        + df["Total QR"]
    )

    daily_data = (
        df[["Record Date", "Total Ridership"]]
        .sort_values("Record Date")
    )

    daily_data["Record Date"] = (
        daily_data["Record Date"]
        .dt.strftime("%Y-%m-%d")
    )

    return daily_data.to_dict(
        orient="records"
    )


def get_peak_period_ridership():
    df = load_ridership_data()

    def classify_period(hour):
        if 7 <= hour <= 10:
            return "Morning Peak"
        elif 11 <= hour <= 16:
            return "Midday"
        elif 17 <= hour <= 20:
            return "Evening Peak"
        else:
            return "Off-Peak"

    df["Period"] = df["Hour"].apply(classify_period)

    period_data = (
        df.groupby("Period")["Ridership"]
        .sum()
        .reset_index()
    )

    period_order = [
        "Morning Peak",
        "Midday",
        "Evening Peak",
        "Off-Peak"
    ]

    period_data["Period"] = pd.Categorical(
        period_data["Period"],
        categories=period_order,
        ordered=True
    )

    period_data = period_data.sort_values("Period")

    return period_data.to_dict(
        orient="records"
    )

def get_station_hour_hotspots(limit=10):
    df = load_ridership_data()

    hotspot_data = (
        df.groupby(["Station", "Hour"])["Ridership"]
        .sum()
        .reset_index()
        .sort_values(
            "Ridership",
            ascending=False
        )
        .head(limit)
    )

    return hotspot_data.to_dict(
        orient="records"
    )


def get_station_crowd_status():
    df = load_ridership_data()

    station_hour_data = (
        df.groupby(["Station", "Hour"])["Ridership"]
        .sum()
        .reset_index()
    )

    def classify_demand(ridership):
        if ridership < 68:
            return "Low"
        elif ridership <= 371:
            return "Moderate"
        else:
            return "High"

    station_hour_data["Demand Status"] = (
        station_hour_data["Ridership"]
        .apply(classify_demand)
    )

    return station_hour_data.to_dict(
        orient="records"
    )


def get_station_flow():
    entries_df = pd.read_csv(
        "../data/bmrcl/station-hourly.csv",
        sep=";"
    )

    exits_df = pd.read_csv(
        "../data/bmrcl/station-hourly-exits.csv",
        sep=";"
    )

    flow_df = pd.merge(
        entries_df,
        exits_df,
        on=["Date", "Hour", "Station"],
        how="inner",
        suffixes=("_entry", "_exit")
    )

    flow_df["Net Flow"] = (
        flow_df["Ridership_entry"]
        - flow_df["Ridership_exit"]
    )

    station_flow = (
        flow_df
        .groupby("Station")[
            ["Ridership_entry", "Ridership_exit", "Net Flow"]
        ]
        .sum()
        .reset_index()
    )

    station_flow = station_flow.sort_values(
        "Net Flow",
        ascending=False
    )

    return station_flow.to_dict(
        orient="records"
    )