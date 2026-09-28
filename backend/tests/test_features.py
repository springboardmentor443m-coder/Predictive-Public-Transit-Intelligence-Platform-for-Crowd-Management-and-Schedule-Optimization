"""Invariants tying the ML feature encoding to the real station data.

`features.STATION_LIST` is baked into trained artifacts, so it has to match
`data/stations.csv` exactly. When the two drift, the one-hot column for a
station silently becomes all-zeros and the model falls back to
population-average behaviour with no error anywhere.
"""

import csv
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ml import features as feat  # noqa: E402

STATIONS_CSV = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "stations.csv"
)


def _csv_rows():
    with open(STATIONS_CSV, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def test_station_list_matches_stations_csv_order():
    assert feat.STATION_LIST == [r["code"] for r in _csv_rows()]


def test_station_list_has_no_duplicates():
    assert len(feat.STATION_LIST) == len(set(feat.STATION_LIST))


def test_max_capacity_covers_the_busiest_station():
    """`cap_norm` is divided by MAX_CAPACITY, so a value below the real maximum
    would normalise past the 1.5 clip and flatten the capacity signal."""
    busiest = max(int(r["capacity_per_hour"]) for r in _csv_rows())
    assert busiest <= feat.MAX_CAPACITY


def test_station_to_features_one_hot_is_exclusive():
    for idx, code in enumerate(feat.STATION_LIST):
        vec = feat.station_to_features(code, 5000)
        assert vec[idx] == 1.0
        assert vec[:len(feat.STATION_LIST)].sum() == 1.0


def test_station_to_features_unknown_station_is_all_zero():
    vec = feat.station_to_features("NOT-A-STATION", 5000)
    assert vec[:len(feat.STATION_LIST)].sum() == 0.0
    # Capacity still contributes, so an unknown stop is not a zero row.
    assert vec[-1] > 0.0


def test_cap_norm_does_not_saturate_at_the_network_maximum():
    busiest = max(int(r["capacity_per_hour"]) for r in _csv_rows())
    assert feat.station_to_features(feat.STATION_LIST[0], busiest)[-1] == pytest.approx(
        busiest / feat.MAX_CAPACITY
    )


def test_row_features_width_is_temporal_plus_station():
    width = len(feat.hour_to_features(8, 2)) + len(feat.STATION_LIST) + 1
    assert len(feat.row_features(8, 2, "128", 11000)) == width


def test_line_slug_is_collision_free_and_fleet_codes_are_unique():
    slugs = [feat.line_slug(r["line"]) for r in _csv_rows()]
    assert len(set(slugs)) == len(set(r["line"] for r in _csv_rows()))

    codes = [
        feat.train_code(line, n)
        for line in set(r["line"] for r in _csv_rows())
        for n in range(1, feat.FLEET_PER_LINE + 1)
    ]
    assert len(codes) == len(set(codes))


def test_rolling_stock_capacities_are_positive():
    assert all(cap > 0 for _, cap in feat.ROLLING_STOCK)


def test_hour_features_are_finite_and_bounded():
    for hour in range(24):
        for weekday in range(7):
            vec = feat.hour_to_features(hour, weekday)
            assert np.all(np.isfinite(vec))
            assert np.all(np.abs(vec) <= 1.0)
