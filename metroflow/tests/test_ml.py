import pytest

from app.services import ai_prediction as ai
from tests.conftest import BUSY, DATE, FUTURE_DATE


@pytest.fixture(scope="module")
def report():
    return ai.get_model_metadata()


def test_report_documents_chronological_evaluation(report):
    p = report["demand"]["periods"]
    assert p["development"][1] < p["test"][0]                      # test strictly after development
    assert all(f[0] > p["development"][0] for f in p["cv_validation_folds"])
    assert len(p["cv_validation_folds"]) == 4


def test_selected_model_has_best_cv_score(report):
    cv = report["demand"]["candidate_cross_validation"]
    best = min(cv, key=lambda n: cv[n]["mean_mae"])
    assert report["demand"]["selected_model"] == best


def test_model_beats_historical_average_on_untouched_test(report):
    d = report["demand"]
    assert d["test_metrics_selected"]["mae"] < d["test_metrics_baseline"]["mae"]
    assert d["improvement_over_baseline_mae_pct"] > 15
    assert d["test_metrics_selected"]["r2"] > 0.99


def test_each_ablation_step_beats_the_baseline_in_cv(report):
    cv = report["demand"]["candidate_cross_validation"]
    base = cv["historical_average_baseline"]["mean_mae"]
    assert cv["profile_plus_holiday_calendar"]["mean_mae"] < cv["profile_plus_week_of_year"]["mean_mae"] < base


def test_interval_coverage_is_close_to_nominal(report):
    cov = report["demand"]["prediction_interval"]["empirical_coverage_on_test_pct"]
    assert 85 <= cov <= 96


def test_anomaly_detector_quality(report):
    a = report["demand"]["anomaly_detector"]
    assert a["false_alarm_rate_on_test_pct"] < 3
    assert a["recall_on_injected_spikes_busy_hours_pct"] >= 95


def test_delay_model_beats_chance(report):
    c = report["delay"]["classifier"]
    assert c["roc_auc"] > 0.55 and c["pr_auc"] > c["pr_auc_random_guess"]
    s = report["delay"]["severity_regressor"]
    assert s["mae_minutes"] < s["mae_minutes_predicting_mean"]


def test_forecast_has_24_hours_with_valid_ranges(client, admin):
    f = client.get(f"/ai/forecast/{BUSY}", headers=admin, params={"on_date": DATE}).json()["forecast"]
    assert [x["hour"] for x in f] == list(range(24))
    for x in f:
        lo, hi = x["predicted_entries_90pct_range"]
        assert 0 <= lo <= x["predicted_entries"] <= hi
        assert 0 <= x["delay_probability"] <= 1 and 0 <= x["predicted_congestion_pct"] <= 100


def test_forecast_learns_rush_hours_and_weekend_shape(client, admin):
    def peak(date):
        f = client.get(f"/ai/forecast/{BUSY}", headers=admin, params={"on_date": date}).json()["forecast"]
        return max(f, key=lambda x: x["predicted_entries"])["hour"], f
    weekday_peak, wd = peak("2023-12-29")   # Friday
    weekend_peak, we = peak("2023-12-30")   # Saturday
    assert weekday_peak in (8, 18) and weekend_peak in (12, 13)
    assert wd[3]["predicted_entries"] < wd[8]["predicted_entries"] / 10


def test_forecast_works_for_future_dates_with_growth(client, admin):
    now = client.get(f"/ai/predict/demand/{BUSY}", headers=admin, params={"on_date": DATE, "hour": 18}).json()
    later = client.get(f"/ai/predict/demand/{BUSY}", headers=admin, params={"on_date": FUTURE_DATE, "hour": 18})
    assert later.status_code == 200
    assert later.json()["predicted_entries"] > 0 and now["predicted_entries"] > 0


def test_holiday_window_is_forecast_lower(client, admin):
    normal = client.get(f"/ai/predict/demand/{BUSY}", headers=admin, params={"on_date": "2023-10-04", "hour": 8}).json()
    holiday = client.get(f"/ai/predict/demand/{BUSY}", headers=admin, params={"on_date": "2023-10-09", "hour": 8}).json()
    assert holiday["predicted_entries"] < normal["predicted_entries"] * 0.9


def test_anomaly_check_flags_spike_and_accepts_normal(client, admin):
    exp = client.get(f"/ai/predict/demand/{BUSY}", headers=admin, params={"on_date": DATE, "hour": 18}).json()["predicted_entries"]
    ok = client.get(f"/ai/anomaly-check/{BUSY}", headers=admin,
                    params={"on_date": DATE, "hour": 18, "observed_entries": exp}).json()
    spike = client.get(f"/ai/anomaly-check/{BUSY}", headers=admin,
                       params={"on_date": DATE, "hour": 18, "observed_entries": exp * 1.5}).json()
    drop = client.get(f"/ai/anomaly-check/{BUSY}", headers=admin,
                      params={"on_date": DATE, "hour": 18, "observed_entries": exp * 0.5}).json()
    assert ok["verdict"] == "NORMAL" and spike["verdict"] == "SPIKE" and drop["verdict"] == "DROP"


def test_detect_anomalies_on_recorded_data_is_mostly_quiet(client, admin):
    r = client.get("/ai/anomalies", headers=admin, params={"on_date": DATE, "hour": 18}).json()
    assert r["stations_checked"] == 30 and len(r["anomalies"]) <= 3


def test_training_is_admin_only(client, operator):
    assert client.post("/ai/train", headers=operator).status_code == 403


def test_recommendations_are_text(client, admin):
    r = client.get(f"/ai/recommendations/{BUSY}", headers=admin, params={"on_date": DATE}).json()
    assert r["recommendations"] and all(isinstance(x, str) for x in r["recommendations"])
