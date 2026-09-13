import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ["MODELS_STORE_DIR"] = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models_store"
)
os.environ["METROFLOW_MODEL_CITY"] = "hangzhou"

import pytest  # noqa: E402

pytest.importorskip("xgboost")

from app.ml import features as feat  # noqa: E402
from app.ml.model_wrappers import CrowdModel, DelayForecaster, DemandForecaster  # noqa: E402


def test_crowd_model_serves_city_artifact():
    m = CrowdModel()
    assert m.is_loaded
    assert m.is_kaggle
    out = m.predict_hourly(8, hours_ahead=6, weekday=2, station={"id": "ST01", "capacity_per_hour": 520})
    assert len(out) == 6
    assert all(0 < p["predicted_occupancy_pct"] <= 120 for p in out)


def test_crowd_prediction_is_not_fallback_baseline():
    m = CrowdModel()
    base = [feat.station_baseline_occupancy_pct((8 + i) % 24) * 100 for i in range(6)]
    out = m.predict_hourly(8, hours_ahead=6, weekday=2, station={"id": "ST01", "capacity_per_hour": 520})
    assert [round(p["predicted_occupancy_pct"], 2) for p in out] != [round(b, 2) for b in base]


def test_demand_model_serves_city_artifact():
    m = DemandForecaster()
    out = m.forecast_hourly(8, hours_ahead=6, weekday=2, station={"id": "ST01", "capacity_per_hour": 520})
    assert len(out) == 6
    assert all(d["predicted_entries"] >= 0 for d in out)


def test_predictions_differ_per_station():
    cm = CrowdModel()
    dm = DemandForecaster()
    a = cm.predict_hourly(8, hours_ahead=6, weekday=2, station={"id": "ST01", "capacity_per_hour": 520})
    b = cm.predict_hourly(8, hours_ahead=6, weekday=2, station={"id": "ST02", "capacity_per_hour": 430})
    assert [p["predicted_occupancy_pct"] for p in a] != [p["predicted_occupancy_pct"] for p in b]
    da = dm.forecast_hourly(8, hours_ahead=6, weekday=2, station={"id": "ST01", "capacity_per_hour": 520})
    db = dm.forecast_hourly(8, hours_ahead=6, weekday=2, station={"id": "ST02", "capacity_per_hour": 430})
    assert [p["predicted_entries"] for p in da] != [p["predicted_entries"] for p in db]


def test_delay_model_serves_artifact():
    m = DelayForecaster()
    if not m.is_loaded:
        pytest.skip("NJ delay artifacts not present")
    out = m.predict(hour=8, weekday=0, sched_minutes=8 * 60 + 30, stop_sequence=1.0,
                    line="Northeast Corrdr", from_station="105", to_station="38187")
    assert out["predicted_delay_minutes"] >= 0
    assert out["delay_bucket"] in m.classes
    assert abs(sum(out["probabilities"].values()) - 1.0) < 1e-3


def test_delay_prediction_differs_by_line():
    m = DelayForecaster()
    if not m.is_loaded:
        pytest.skip("NJ delay artifacts not present")
    a = m.predict(hour=8, weekday=0, sched_minutes=8 * 60 + 30, stop_sequence=1.0,
                  line="Princeton Shuttle", from_station="105", to_station="38187")
    b = m.predict(hour=8, weekday=0, sched_minutes=8 * 60 + 30, stop_sequence=1.0,
                  line="Atl. City Line", from_station="107", to_station="63")
    assert a != b


def test_delay_model_raises_without_artifacts():
    m = DelayForecaster()
    m.artifact = None
    m.regressor = None
    with pytest.raises(RuntimeError):
        m.predict(hour=8, weekday=0, sched_minutes=510, stop_sequence=1.0,
                  line="Northeast Corrdr", from_station="105", to_station="38187")