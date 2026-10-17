import pandas as pd


# Earlier records are incomplete. Keep this equal to PREDICTION_START_DATE in
# prediction_service.py so totals and the model use the same data window.
DATA_START_DATE = pd.Timestamp("2025-08-12")

DATA_PATH = "../data/bmrcl/station-hourly.csv"
EXITS_DATA_PATH = "../data/bmrcl/station-hourly-exits.csv"


def load_ridership_data():
    """Load historical station-hour ridership data."""
    df = pd.read_csv(DATA_PATH, sep=";")
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["Hour"] = pd.to_numeric(df["Hour"], errors="coerce")
    df["Ridership"] = pd.to_numeric(df["Ridership"], errors="coerce")

    df = df.dropna(subset=["Date", "Hour", "Station", "Ridership"])
    df["Hour"] = df["Hour"].astype(int)
    df = df[df["Hour"].between(0, 23)]

    return df


def get_station_ridership():
    """Return station totals and average historical hourly ridership."""
    df = load_ridership_data()

    station_data = (
        df.groupby("Station")
        .agg(
            Ridership=("Ridership", "sum"),
            Average=("Ridership", "mean"),
        )
        .reset_index()
        .sort_values("Ridership", ascending=False)
    )

    station_data["Ridership"] = (
        station_data["Ridership"].round(0).astype(int)
    )
    station_data["Average"] = station_data["Average"].round(2)

    return station_data.to_dict(orient="records")


def get_hourly_ridership():
    """Return total historical ridership by hour."""
    df = load_ridership_data()

    hourly_data = (
        df.groupby("Hour")["Ridership"]
        .sum()
        .reset_index()
        .sort_values("Hour")
    )

    hourly_data["Ridership"] = (
        hourly_data["Ridership"].round(0).astype(int)
    )

    return hourly_data.to_dict(orient="records")


def get_daily_ridership():
    """Return daily ridership from the daily ridership dataset."""
    df = pd.read_csv("../data/bmrcl/daily-ridership.csv")

    df["Record Date"] = pd.to_datetime(
        df["Record Date"],
        format="%d-%m-%Y",
        errors="coerce",
    )

    ridership_columns = [
        "Total Smart Cards",
        "Total Tokens",
        "Total NCMC",
        "Group Ticket",
        "Total QR",
    ]

    for column in ridership_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce").fillna(0)

    df["Total Ridership"] = df[ridership_columns].sum(axis=1)

    daily_data = (
        df[["Record Date", "Total Ridership"]]
        .dropna(subset=["Record Date"])
        .sort_values("Record Date")
        .copy()
    )

    daily_data["Record Date"] = (
        daily_data["Record Date"].dt.strftime("%Y-%m-%d")
    )

    return daily_data.to_dict(orient="records")


def get_peak_period_ridership():
    """Return historical ridership grouped by time period."""
    df = load_ridership_data()

    def classify_period(hour):
        if 7 <= hour <= 10:
            return "Morning Peak"
        elif 11 <= hour <= 16:
            return "Midday"
        elif 17 <= hour <= 20:
            return "Evening Peak"
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
        "Off-Peak",
    ]

    period_data["Period"] = pd.Categorical(
        period_data["Period"],
        categories=period_order,
        ordered=True,
    )

    period_data = period_data.sort_values("Period")

    return period_data.to_dict(orient="records")


def _sum_by_station_hour(df):
    """Total ridership per station and hour of day, summed over all dates.

    Also reports how many distinct dates contributed to each bucket and the
    average per observed day. Missing records are never counted as zero.
    Only dates on or after DATA_START_DATE are used.
    """
    df = df[pd.to_datetime(df["Date"], errors="coerce") >= DATA_START_DATE]

    grouped = (
        df.groupby(["Station", "Hour"])
        .agg(
            Ridership=("Ridership", "sum"),
            Days_Observed=("Date", "nunique"),
        )
        .reset_index()
        .rename(columns={"Days_Observed": "Days Observed"})
    )

    observed_days = grouped["Days Observed"].where(
        grouped["Days Observed"] > 0
    )

    grouped["Average Daily Ridership"] = (
        grouped["Ridership"].div(observed_days).round(2)
    )

    return grouped


def get_station_hour_hotspots(limit=10):
    """Return the highest station-hour ridership totals (summed over dates)."""
    df = load_ridership_data()

    hotspot_data = (
        _sum_by_station_hour(df)
        .sort_values("Ridership", ascending=False)
        .head(limit)
    )

    return hotspot_data.to_dict(orient="records")


def _build_station_hour_demand():
    """Calculate relative demand categories for each station and hour."""
    df = load_ridership_data()

    station_hour_data = _sum_by_station_hour(df)

    station_hour_data["P25"] = (
        station_hour_data.groupby("Station")["Ridership"]
        .transform(lambda values: values.quantile(0.25))
    )

    station_hour_data["P75"] = (
        station_hour_data.groupby("Station")["Ridership"]
        .transform(lambda values: values.quantile(0.75))
    )

    station_hour_data["Demand Status"] = "Moderate"

    station_hour_data.loc[
        station_hour_data["Ridership"] <= station_hour_data["P25"],
        "Demand Status",
    ] = "Low"

    station_hour_data.loc[
        station_hour_data["Ridership"] > station_hour_data["P75"],
        "Demand Status",
    ] = "High"

    return station_hour_data


def get_station_crowd_status():
    """Return historical station-hour demand categories."""
    station_hour_data = _build_station_hour_demand()

    return station_hour_data[
        [
            "Station",
            "Hour",
            "Ridership",
            "Demand Status",
            "Days Observed",
            "Average Daily Ridership",
        ]
    ].to_dict(orient="records")


def get_station_flow():
    """Return historical entries, exits, and net flow by station."""
    entries_df = load_ridership_data()

    exits_df = pd.read_csv(EXITS_DATA_PATH, sep=";")
    exits_df["Date"] = pd.to_datetime(exits_df["Date"], errors="coerce")
    exits_df["Hour"] = pd.to_numeric(exits_df["Hour"], errors="coerce")
    exits_df["Ridership"] = pd.to_numeric(
        exits_df["Ridership"], errors="coerce"
    )

    exits_df = exits_df.dropna(
        subset=["Date", "Hour", "Station", "Ridership"]
    )
    exits_df["Hour"] = exits_df["Hour"].astype(int)

    flow_df = pd.merge(
        entries_df,
        exits_df,
        on=["Date", "Hour", "Station"],
        how="inner",
        suffixes=("_entry", "_exit"),
    )

    flow_df = flow_df[flow_df["Date"] >= DATA_START_DATE].copy()

    flow_df["Net Flow"] = (
        flow_df["Ridership_entry"] - flow_df["Ridership_exit"]
    )

    station_flow = (
        flow_df.groupby("Station")[
            ["Ridership_entry", "Ridership_exit", "Net Flow"]
        ]
        .sum()
        .reset_index()
        .sort_values("Net Flow", ascending=False)
    )

    return station_flow.to_dict(orient="records")


def get_station_crowd_heatmap():
    """Return historical station-hour demand status."""
    station_hour_data = _build_station_hour_demand()

    station_hour_data = station_hour_data.drop(
        columns=["P25", "P75"]
    ).sort_values(["Station", "Hour"])

    return station_hour_data[
        [
            "Station",
            "Hour",
            "Ridership",
            "Demand Status",
            "Days Observed",
            "Average Daily Ridership",
        ]
    ].to_dict(orient="records")


def get_station_demand_pressure():
    """Return relative demand pressure and station average comparisons."""
    station_hour_data = _build_station_hour_demand()

    station_hour_data["Demand Pressure"] = (
        station_hour_data.groupby("Station")["Ridership"]
        .rank(method="average", pct=True)
        .mul(100)
        .round(2)
    )

    station_hour_data["Station Average Ridership"] = (
        station_hour_data.groupby("Station")["Ridership"]
        .transform("mean")
        .round(2)
    )

    station_average = station_hour_data[
        "Station Average Ridership"
    ].where(
        station_hour_data["Station Average Ridership"] != 0
    )

    station_hour_data["Demand vs Average (%)"] = (
        (
            station_hour_data["Ridership"]
            - station_hour_data["Station Average Ridership"]
        )
        .div(station_average)
        .mul(100)
        .round(2)
    )

    return station_hour_data[
        [
            "Station",
            "Hour",
            "Ridership",
            "Demand Status",
            "Demand Pressure",
            "Station Average Ridership",
            "Demand vs Average (%)",
            "Days Observed",
            "Average Daily Ridership",
        ]
    ].to_dict(orient="records")
