"""The NYC artifacts must match the feature encoding exactly.

These are the failures that produce a *silently* degraded app: a shape mismatch
raises inside `predict`, the exception is caught, and the rule-based baseline is
returned instead — while `/predictions/model-info` still reports the model as
loaded. Nothing looks broken, the predictions are just not the model's.
"""

import os
import sys

import numpy as np

os.environ["DATABASE_URL"] = "sqlite:///./test_ml_artifacts.db"
os.environ["MONGODB_URL"] = ""
os.environ["REDIS_URL"] = ""

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest  # noqa: E402

from app.core.time import city_hour, city_weekday  # noqa: E402
from app.ml import features as feat  # noqa: E402
from app.ml.model_wrappers import CrowdModel, DemandForecaster  # noqa: E402

EXPECTED_WIDTH = len(feat.hour_to_features(0, 0)) + len(feat.STATION_LIST) + 1


@pytest.fixture(scope="module")
def crowd():
    return CrowdModel()


@pytest.fixture(scope="module")
def demand():
    return DemandForecaster()


@pytest.fixture(scope="module")
def station():
    return {"id": feat.STATION_LIST[0], "capacity_per_hour": 11000}


def test_nyc_artifacts_are_the_ones_loaded(crowd, demand):
    """`_city_file` prefers `nyc_*` once METROFLOW_MODEL_CITY=nyc. Falling back to
    the legacy 10-station artifact is what broke inference."""
    assert crowd.is_loaded, "crowd artifact missing - run scripts/train_models.py"
    assert demand.is_loaded, "demand artifact missing - run scripts/train_models.py"
    assert crowd.trained_on == "nyc"
    assert demand.trained_on == "nyc"
    assert crowd.is_kaggle and demand.is_kaggle


def test_artifact_station_list_matches_the_encoder(crowd, demand):
    assert crowd.stations == feat.STATION_LIST
    assert demand.stations == feat.STATION_LIST


def test_encoder_width_matches_the_estimator(crowd, station):
    X = crowd._feature_rows([8], [0], station)
    assert X.shape[1] == EXPECTED_WIDTH
    assert crowd.artifact["model"].n_features_in_ == EXPECTED_WIDTH


def test_cap_norm_scale_is_not_the_legacy_value(crowd):
    """The old artifacts carried cap_norm_scale=700, which saturated cap_norm for
    every station once real capacities reached the thousands."""
    assert crowd.cap_norm_scale == feat.MAX_CAPACITY
    assert crowd.cap_norm_scale > 7000


def test_capacity_actually_varies_the_encoding(crowd, station):
    """cap_norm must be a live feature, not a constant every row shares."""
    busy = dict(station, capacity_per_hour=14600)
    quiet = dict(station, capacity_per_hour=1350)
    a = crowd._feature_rows([8], [0], busy)[0, -1]
    b = crowd._feature_rows([8], [0], quiet)[0, -1]
    assert a != b
    assert a > b


def test_happy_path_matches_a_direct_estimator_call(crowd, station):
    """The strongest guard against silent fallback: if `predict` ever stops calling
    the estimator and starts using the rule-based baseline, the returned numbers no
    longer equal what the artifact produces. It still *looks* healthy."""
    from datetime import datetime

    anchor = datetime(2026, 9, 28, 12)  # 12:00Z == 08:00 local
    out = crowd.predict_period(anchor, 3, station)
    # Resolved through the city helpers, exactly as predict_period does. Using
    # `anchor.hour` here would compare the model against a *different* feature
    # vector and this guard would fail for the wrong reason.
    direct = crowd.artifact["model"].predict(
        np.array([feat.row_features(
            city_hour(anchor), city_weekday(anchor),
            station["id"], station["capacity_per_hour"],
        )])
    )
    # The artifact is trained on occupancy/capacity as a 0-1 fraction
    # (train_models.py) and predict_period scales it to 0-100 for the API, then
    # rounds to 2dp. Asserting the conversion keeps the two from drifting apart;
    # the tolerance is that rounding step.
    assert abs(out[0]["predicted_occupancy_pct"] - float(direct[0]) * 100) <= 0.01


def test_a_failing_estimator_degrades_to_baseline_instead_of_500ing(crowd, station, monkeypatch, caplog):
    """Resilience contract: one bad row must not take down the dashboard. It must
    also log, because a swallowed failure is indistinguishable from success."""
    from datetime import datetime

    def boom(_X):
        raise ValueError("corrupt row width")

    monkeypatch.setattr(crowd.artifact["model"], "predict", boom)
    with caplog.at_level("WARNING", logger="app.ml.model_wrappers"):
        out = crowd.predict_period(datetime(2026, 9, 28, 12), 3, station)
    assert len(out) == 3
    assert all(0 <= p["predicted_occupancy_pct"] <= 120 for p in out)
    assert any("falling back" in r.message or "baseline" in r.message for r in caplog.records)


class TestDegradationIsReported:
    """A degraded pipeline has to be visible, not merely logged.

    Previously the wrapper returned the baseline curve and the dashboard still
    rendered a green "Live Serving" badge, because `is_loaded` only described
    load-time success. The UI now renders from `degraded`, so these assertions
    guard the contract the UI depends on.

    The shared `crowd` fixture is module-scoped, which is right for read-only
    prediction tests but wrong here: the degradation flag is sticky by design
    (a transient blip must not flap the dashboard back to green), so a fresh
    instance is required per test.
    """

    @pytest.fixture
    def fresh_crowd(self):
        return CrowdModel()

    def test_a_healthy_artifact_is_not_degraded(self, fresh_crowd):
        assert fresh_crowd.is_loaded is True
        assert fresh_crowd.degraded is False
        assert fresh_crowd.degraded_reason is None
        assert fresh_crowd.serving_state()["runtime_fallbacks"] == 0

    def test_degradation_is_sticky_across_calls(self, fresh_crowd, station, monkeypatch):
        """Once serving from the baseline, it must not quietly return to green."""
        from datetime import datetime

        def boom(_X):
            raise RuntimeError("transient")

        monkeypatch.setattr(fresh_crowd.artifact["model"], "predict", boom)
        fresh_crowd.predict_period(datetime(2026, 9, 28, 12), 2, station)
        assert fresh_crowd.degraded is True
        # Even if the estimator starts working again, the operator should still
        # see the incident until it is investigated or the process restarts.
        monkeypatch.undo()
        fresh_crowd.predict_period(datetime(2026, 9, 28, 12), 2, station)
        assert fresh_crowd.degraded is True

    def test_runtime_failure_marks_the_model_degraded(self, fresh_crowd, station, monkeypatch):
        from datetime import datetime

        def boom(_X):
            raise RuntimeError("estimator exploded")

        monkeypatch.setattr(fresh_crowd.artifact["model"], "predict", boom)
        fresh_crowd.predict_period(datetime(2026, 9, 28, 12), 3, station)

        # `is_loaded` still True - the artifact is present - but it is not serving.
        assert fresh_crowd.is_loaded is True
        assert fresh_crowd.degraded is True
        # The public reason is sanitized: the dashboard shows the model fell back,
        # but the operator's exception text stays in the logs, not in the API.
        assert fresh_crowd.degraded_reason == "runtime fallback: model raised an error during prediction"
        assert "estimator exploded" not in (fresh_crowd.degraded_reason or "")
        state = fresh_crowd.serving_state()
        assert state["degraded"] is True
        assert state["runtime_fallbacks"] == 1

    def test_repeated_failures_are_counted(self, fresh_crowd, station, monkeypatch):
        from datetime import datetime

        def boom(_X):
            raise RuntimeError("still broken")

        monkeypatch.setattr(fresh_crowd.artifact["model"], "predict", boom)
        for _ in range(3):
            fresh_crowd.predict_period(datetime(2026, 9, 28, 12), 2, station)
        assert fresh_crowd.serving_state()["runtime_fallbacks"] == 3

    def test_a_missing_artifact_is_degraded_from_the_start(self, monkeypatch, station):
        from app.ml.model_wrappers import CrowdModel

        monkeypatch.setattr("app.ml.model_wrappers._load_artifact", lambda _f: None)
        model = CrowdModel()
        assert model.is_loaded is False
        assert model.degraded is True
        # Still answers with a usable, bounded curve.
        out = model.predict_hourly(8, 3, 0, station)
        assert len(out) == 3
        assert all(0 <= p["predicted_occupancy_pct"] <= 120 for p in out)

    def test_demand_model_reports_degradation_too(self, monkeypatch, station):
        from app.ml.model_wrappers import DemandForecaster

        monkeypatch.setattr("app.ml.model_wrappers._load_artifact", lambda _f: None)
        model = DemandForecaster()
        assert model.degraded is True
        assert model.degraded_reason


def test_predictions_span_the_congestion_bands(crowd, station):
    """A model that never leaves 'low' cannot drive the congestion UI."""
    from datetime import datetime

    out = crowd.predict_period(datetime(2026, 9, 28, 0), 24, station)
    levels = {p["congestion_level"] for p in out}
    assert len(levels) >= 3, f"only produced {levels}"
    assert any(p["predicted_occupancy_pct"] >= 75 for p in out)
    assert any(p["predicted_occupancy_pct"] < 55 for p in out)


def test_predictions_are_ordered_lower_center_upper(crowd, station):
    from datetime import datetime

    for p in crowd.predict_period(datetime(2026, 9, 28, 6), 6, station):
        assert p["lower"] <= p["predicted_occupancy_pct"] + 1e-6
        assert p["upper"] >= p["predicted_occupancy_pct"] - 1e-6
        assert 0 <= p["lower"] <= p["upper"] <= 100


def test_weekend_is_quieter_than_the_matching_weekday(crowd, station):
    from datetime import datetime

    sat = crowd.predict_period(datetime(2026, 9, 26, 8), 3, station)
    mon = crowd.predict_period(datetime(2026, 9, 28, 8), 3, station)
    sat_total = sum(p["predicted_occupancy_pct"] for p in sat)
    mon_total = sum(p["predicted_occupancy_pct"] for p in mon)
    assert sat_total < mon_total


def test_demand_predictions_are_positive_integers(demand, station):
    from datetime import datetime

    for p in demand.forecast_period(datetime(2026, 9, 28, 7), 6, station):
        assert p["predicted_entries"] > 0
        assert p["predicted_exits"] > 0
        assert isinstance(p["predicted_entries"], int)


def test_busier_stations_predict_higher_demand(demand):
    from datetime import datetime

    quiet = demand.forecast_period(
        datetime(2026, 9, 28, 8), 1, {"id": feat.STATION_LIST[0], "capacity_per_hour": 1350}
    )
    busy = demand.forecast_period(
        datetime(2026, 9, 28, 8), 1, {"id": feat.STATION_LIST[0], "capacity_per_hour": 14600}
    )
    assert busy[0]["predicted_entries"] > quiet[0]["predicted_entries"]


def test_unknown_station_still_predicts(crowd, station):
    """An unrecognised code must not raise - it encodes as population-average."""
    from datetime import datetime

    out = crowd.predict_period(
        datetime(2026, 9, 28, 8), 2, {"id": "NOT-A-STATION", "capacity_per_hour": 5000}
    )
    assert len(out) == 2
    assert all(0 <= p["predicted_occupancy_pct"] <= 120 for p in out)
