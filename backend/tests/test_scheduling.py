"""
tests/test_scheduling.py
Real, passing tests on the actual capacity/crowd/alert logic in
model/scheduling.py. These test genuine behavior, including a
regression test for a real bug found and fixed during development
(see test_capacity_multiplier_reaches_high_band).

Run from the backend/ folder:
  pytest tests/ -v
"""

import sys
import os
import pandas as pd
import pytest

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "model"))
from scheduling import (
    build_capacity_table, crowd_percent, crowd_level, recommendation,
    simulate_headway_minutes, simulate_next_arrivals, simulate_delay_minutes,
    delay_alert, LOW_PCT, HIGH_PCT,
)


@pytest.fixture
def sample_df():
    """A tiny synthetic dataframe mimicking two stations with different peaks."""
    return pd.DataFrame({
        "station": ["A", "A", "A", "B", "B", "B"],
        "passenger_count": [100, 500, 1000, 50, 200, 300],
    })


def test_capacity_is_per_station_not_shared(sample_df):
    """Each station must get its OWN capacity - this was an explicit
    mentor requirement, not one shared number across all stations."""
    capacity_table = build_capacity_table(sample_df)
    assert capacity_table["A"] != capacity_table["B"]
    assert capacity_table["A"] == round(1000 * 1.1)
    assert capacity_table["B"] == round(300 * 1.1)


def test_capacity_multiplier_reaches_high_band(sample_df):
    """
    Regression test for a real bug found during development: an earlier
    version used a 1.3x capacity multiplier, which made the 'high' crowd
    band mathematically unreachable (even a station's own peak hour would
    fall under 80% of a 1.3x-padded capacity). This test locks in that
    the CURRENT multiplier (1.1x) allows a station's peak hour to
    correctly reach the 'high' band.
    """
    capacity_table = build_capacity_table(sample_df)
    peak_count_for_a = 1000
    pct = crowd_percent(peak_count_for_a, "A", capacity_table)
    assert pct >= HIGH_PCT * 100, (
        f"A station's own peak hour should reach the 'high' band, got {pct}%"
    )
    assert crowd_level(pct) == "high"


def test_crowd_level_bands(sample_df):
    capacity_table = build_capacity_table(sample_df)
    capacity = capacity_table["A"]  # 1100

    just_under_low = capacity * 0.49
    at_medium = capacity * 0.55
    at_high = capacity * 0.85

    assert crowd_level(crowd_percent(int(just_under_low), "A", capacity_table)) == "low"
    assert crowd_level(crowd_percent(int(at_medium), "A", capacity_table)) == "medium"
    assert crowd_level(crowd_percent(int(at_high), "A", capacity_table)) == "high"


def test_recommendation_sets_overcrowding_alert_only_on_high(sample_df):
    capacity_table = build_capacity_table(sample_df)
    low_rec = recommendation(50, "A", capacity_table)
    high_rec = recommendation(1000, "A", capacity_table)

    assert low_rec["overcrowding_alert"] is False
    assert high_rec["overcrowding_alert"] is True


def test_unknown_station_returns_zero_percent():
    """A station not in the capacity table shouldn't crash - should
    safely return 0% rather than raising an error."""
    pct = crowd_percent(500, "NonexistentStation", {"A": 1000})
    assert pct == 0.0


def test_headway_shorter_at_peak_hours():
    assert simulate_headway_minutes(9) < simulate_headway_minutes(2)   # morning peak vs late night
    assert simulate_headway_minutes(18) < simulate_headway_minutes(13)  # evening peak vs midday


def test_next_arrivals_list_length_and_order():
    arrivals = simulate_next_arrivals(hour=18, n=3)
    assert len(arrivals) == 3
    assert arrivals == sorted(arrivals)  # arrival times should increase


def test_delay_increases_with_crowd_pct():
    low_delay = simulate_delay_minutes(crowd_pct=40, seed=1)
    high_delay = simulate_delay_minutes(crowd_pct=95, seed=1)
    assert high_delay > low_delay


def test_delay_alert_threshold():
    assert delay_alert(delay_minutes=1.0) is False
    assert delay_alert(delay_minutes=5.0) is True
