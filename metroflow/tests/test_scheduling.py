from app.services.scheduling import FREQUENCY_TABLE
from tests.conftest import BUSY, DATE


def test_schedule_has_24_rows_with_consistent_frequency(client, admin):
    s = client.get(f"/schedule/{BUSY}", headers=admin, params={"on_date": DATE}).json()["schedule"]
    assert len(s) == 24
    for row in s:
        assert row["recommended_frequency_min"] == FREQUENCY_TABLE[row["congestion_band"]]


def test_trains_run_more_often_at_peak_than_overnight(client, admin):
    s = {r["hour"]: r for r in client.get(f"/schedule/{BUSY}", headers=admin, params={"on_date": DATE}).json()["schedule"]}
    assert s[8]["recommended_frequency_min"] < s[3]["recommended_frequency_min"]


def test_peak_summary(client, admin):
    p = client.get(f"/schedule/{BUSY}/peak-summary", headers=admin, params={"on_date": DATE}).json()
    assert p["peak_hour"] in (8, 18) and p["off_peak_hours"] and 3 in p["off_peak_hours"]


def test_delay_report(client, admin):
    d = client.get(f"/schedule/{BUSY}/delay-report", headers=admin).json()
    assert d["delay_events"] > 0 and 0 < d["avg_delay_minutes"] <= d["max_delay_minutes"]


def test_delay_adjustment_tightens_frequency(client, admin):
    base = {"on_date": DATE, "hour": 8}
    none = client.get(f"/schedule/{BUSY}/adjust-for-delay", headers=admin, params={**base, "delay_minutes": 0}).json()
    small = client.get(f"/schedule/{BUSY}/adjust-for-delay", headers=admin, params={**base, "delay_minutes": 5}).json()
    big = client.get(f"/schedule/{BUSY}/adjust-for-delay", headers=admin, params={**base, "delay_minutes": 20}).json()
    assert none["adjusted_frequency_min"] == none["original_recommended_frequency_min"]
    assert big["adjusted_frequency_min"] < small["adjusted_frequency_min"] < none["adjusted_frequency_min"]
    assert big["delay_source"] == "reported by operator"


def test_delay_scenario_without_input_uses_model(client, admin):
    r = client.get(f"/schedule/{BUSY}/adjust-for-delay", headers=admin, params={"on_date": DATE, "hour": 8}).json()
    assert r["delay_minutes_used"] > 0 and r["delay_source"].startswith("model scenario")
