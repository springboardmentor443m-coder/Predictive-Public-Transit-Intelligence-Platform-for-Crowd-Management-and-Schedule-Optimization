from app.data import repository as repo


def test_ridership_schema_and_span():
    df = repo.load_data()
    assert {"Date", "Hour", "Station", "Entries", "Exits"} <= set(df.columns)
    assert df["Station"].nunique() == 30
    assert str(df["Date"].min().date()) == "2022-01-01" and str(df["Date"].max().date()) == "2023-12-31"
    assert len(df) == 730 * 24 * 30


def test_no_missing_or_negative_values():
    df = repo.load_data()
    assert df[["Entries", "Exits"]].notna().all().all()
    assert (df["Entries"] >= 0).all() and (df["Exits"] >= 0).all()
    assert df["Hour"].between(0, 23).all()


def test_every_station_has_capacity():
    cap = repo.load_capacity()
    assert set(repo.list_stations()) == set(cap)
    assert all(v > 0 for v in cap.values())
    assert cap["Taipei Main Station"] > cap["Taipei Zoo"]  # capacity differs by station size


def test_delays_reference_real_stations_and_valid_minutes():
    delays = repo.load_delays()
    assert set(delays["Station"]) <= set(repo.list_stations())
    assert delays["DelayMinutes"].between(1, 35).all()


def test_rush_hour_shape_weekday():
    df = repo.load_data()
    wd = df[(df["Station"] == "Taipei Main Station") & (~df["is_weekend"])]
    by_hour = wd.groupby("Hour")["Entries"].mean()
    assert by_hour.idxmax() in (8, 18)
    assert by_hour[3] < by_hour[8] / 20  # overnight is almost empty


def test_delays_rise_with_congestion():
    """The generator ties delay frequency to crowding: busy station-hours see more delays."""
    df = repo.load_data()[["Date", "Hour", "Station", "Entries"]]
    d = repo.load_delays()[["Date", "Hour", "Station"]].assign(delayed=1)
    m = df.merge(d, on=["Date", "Hour", "Station"], how="left").fillna({"delayed": 0})
    m["cong"] = m["Entries"] / m["Station"].map(repo.load_capacity())
    low, high = m[m["cong"] < 0.1]["delayed"].mean(), m[m["cong"] > 0.4]["delayed"].mean()
    assert high > low
