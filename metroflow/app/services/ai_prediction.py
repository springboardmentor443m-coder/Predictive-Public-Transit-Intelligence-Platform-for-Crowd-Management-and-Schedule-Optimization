"""
AI Prediction Module: demand forecasting, delay-risk modelling, anomaly detection.

How the ML pipeline is set up (and why)
---------------------------------------
1. Chronological evaluation. The data is a time series, so a random split would
   leak the future into training. The final ~17% of the timeline is held back as
   an untouched TEST period. Model selection uses expanding-window time-series
   cross-validation on the earlier ~83% (train on the past, validate on the next
   block, four times), so the folds cover both public-holiday periods instead of
   one arbitrary window. The chosen model is refit on the development period for
   the test score, then on all data for deployment.

2. Candidate models are compared by mean cross-validated MAE:
       historical_average_baseline        mean demand per (station, hour, weekday)
       profile_plus_trend_seasonality     baseline x (growth trend + yearly seasonality)
       profile_plus_week_of_year          ... + week-of-year effects
       profile_plus_holiday_calendar      ... + public-holiday windows
       gradient_boosting_direct           HistGradientBoosting on raw calendar features
   The comparison table doubles as an ablation: each step shows what one added
   ingredient is worth.

3. Prediction intervals use the Anscombe variance-stabilising transform
   (2*sqrt(x + 3/8)), because passenger counts behave like Poisson counts: busy
   stations are noisier in absolute terms and quiet hours are skewed. After the
   transform the forecast error has roughly constant spread, so one calibrated
   quantile works for every station and hour. The quantile is calibrated on the
   most recent out-of-fold residuals and its coverage is then checked on the untouched test
   period.

4. Delays are rare (~2% of station-hours), so a two-stage model is used: a
   classifier for "will a delay happen this hour" and a regressor for "how long
   if it does". The classifier is judged with ROC-AUC, PR-AUC and Brier score
   against a constant base-rate predictor, not accuracy, which is misleading
   for rare events.

5. Anomaly detection reuses the demand model: an observation is flagged when it
   sits more than 3 sigma away from the forecast (sigma estimated from
   out-of-fold residuals). Its false-alarm rate and its recall on injected
   spikes are measured on the test period.

POST /ai/train re-runs the whole pipeline and rewrites model_metadata.json.
"""
import json
import threading
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import (average_precision_score, brier_score_loss, mean_absolute_error,
                             mean_squared_error, r2_score, roc_auc_score)
from sklearn.preprocessing import LabelEncoder

from app.data import repository as repo

MODEL_DIR = Path(__file__).resolve().parents[1] / "ml_artifacts"
DEMAND_MODEL_PATH = MODEL_DIR / "demand_model.joblib"
DELAY_MODEL_PATH = MODEL_DIR / "delay_model.joblib"
METADATA_PATH = MODEL_DIR / "model_metadata.json"

# Public-holiday calendar: windows that are known in advance. For real data, load the
# official holiday calendar here (start and end as month*100 + day).
HOLIDAY_WINDOWS = {
    "lunar_new_year_break": (201, 210),
    "national_day_break": (1008, 1010),
}

DEV_END_FRAC = 0.83     # development period = first 83% of the timeline; the rest is test
CV_BLOCKS = 6           # development period is cut into 6 blocks ...
CV_FOLDS = 4            # ... and the last 4 blocks are each used once as a validation fold
CALIBRATION_FOLDS = 2   # most recent folds used to calibrate intervals / anomaly sigma
ANOMALY_Z = 3.0
EPOCH = pd.Timestamp("2022-01-01")


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------
def _with_calendar(df: pd.DataFrame) -> pd.DataFrame:
    """Frame needs columns Date (datetime), Station, Hour. Adds calendar fields."""
    d = df.copy()
    d["day_of_week"] = d["Date"].dt.dayofweek
    d["month"] = d["Date"].dt.month
    d["is_weekend"] = (d["day_of_week"] >= 5).astype(int)
    return d


def _calendar_features(dates: pd.Series, use_weeks: bool, use_holidays: bool = False) -> pd.DataFrame:
    """Growth trend + yearly seasonality (+ week-of-year effects, + holiday windows)."""
    t = (dates - EPOCH).dt.days.values.astype(float)
    doy = dates.dt.dayofyear.values
    cols = {"trend_years": t / 365.0}
    for k in (1, 2):
        cols[f"sin{k}"] = np.sin(2 * np.pi * k * doy / 365.25)
        cols[f"cos{k}"] = np.cos(2 * np.pi * k * doy / 365.25)
    X = pd.DataFrame(cols)
    if use_weeks:
        week = np.minimum((doy - 1) // 7, 51)
        for i in range(52):
            X[f"week{i}"] = (week == i).astype(float)
    if use_holidays:
        md = dates.dt.month.values * 100 + dates.dt.day.values
        for name, (start, end) in HOLIDAY_WINDOWS.items():
            X[name] = ((md >= start) & (md <= end)).astype(float)
    return X


def _metrics(y_true, y_pred) -> dict:
    y_true, y_pred = np.asarray(y_true, dtype=float), np.asarray(y_pred, dtype=float)
    return {
        "mae": round(float(mean_absolute_error(y_true, y_pred)), 2),
        "rmse": round(float(np.sqrt(mean_squared_error(y_true, y_pred))), 2),
        "wape_pct": round(float(np.abs(y_true - y_pred).sum() / max(y_true.sum(), 1) * 100), 2),
        "r2": round(float(r2_score(y_true, y_pred)), 4),
    }


def _dev_test_split(df: pd.DataFrame):
    """Development period (first ~83%) and untouched test period (last ~17%)."""
    dates = np.sort(df["Date"].unique())
    cut = dates[int(len(dates) * DEV_END_FRAC)]
    dev, test = df[df["Date"] < cut], df[df["Date"] >= cut]
    return dev, test


def _period(d: pd.DataFrame) -> list:
    return [str(d["Date"].min().date()), str(d["Date"].max().date())]


def _cv_folds(dev: pd.DataFrame):
    """Expanding-window folds: train on everything before a block, validate on the block."""
    dates = np.sort(dev["Date"].unique())
    edges = np.linspace(0, len(dates), CV_BLOCKS + 1).astype(int)
    for k in range(CV_BLOCKS - CV_FOLDS, CV_BLOCKS):
        start, end = dates[edges[k]], (dates[edges[k + 1]] if edges[k + 1] < len(dates) else None)
        train = dev[dev["Date"] < start]
        val = dev[(dev["Date"] >= start) & ((dev["Date"] < end) if end is not None else True)]
        yield train, val


# ---------------------------------------------------------------------------
# Demand models (all expose fit(df) / predict(df) on Date, Station, Hour frames)
# ---------------------------------------------------------------------------
class HistoricalAverageBaseline:
    """Mean entries per (station, hour, weekday) over the training period."""

    def fit(self, df: pd.DataFrame):
        d = _with_calendar(df)
        self.profile_ = (d.groupby(["Station", "Hour", "day_of_week"])["Entries"]
                         .mean().rename("profile").reset_index())
        self.fallback_ = float(d["Entries"].mean())
        return self

    def _profile(self, d: pd.DataFrame) -> np.ndarray:
        merged = d.merge(self.profile_, on=["Station", "Hour", "day_of_week"], how="left")
        return merged["profile"].fillna(self.fallback_).values

    def predict(self, df: pd.DataFrame) -> np.ndarray:
        return self._profile(_with_calendar(df))


class ProfileCalendarModel(HistoricalAverageBaseline):
    """Station/hour/weekday profile x a learned calendar multiplier.

    The profile captures *who travels when*; a ridge regression on the daily
    ratio (actual / profile) captures *how busy the whole network is on that
    date*: growth trend, yearly seasonality and optionally week-of-year effects.
    Being linear in the trend, it can extrapolate growth into the future,
    which tree models cannot do.
    """

    def __init__(self, use_weeks: bool, use_holidays: bool = False):
        self.use_weeks = use_weeks
        self.use_holidays = use_holidays

    def fit(self, df: pd.DataFrame):
        super().fit(df)
        d = _with_calendar(df)
        d = d.assign(profile=self._profile(d))
        daily = d.groupby("Date").agg(actual=("Entries", "sum"), profile=("profile", "sum")).reset_index()
        ratio = daily["actual"] / daily["profile"]
        weights = daily["profile"] / daily["profile"].mean()
        self.calendar_ = Ridge(alpha=1.0).fit(
            _calendar_features(daily["Date"], self.use_weeks, self.use_holidays), ratio,
            sample_weight=weights)
        return self

    def predict(self, df: pd.DataFrame) -> np.ndarray:
        d = _with_calendar(df)
        base = self._profile(d)
        unique_dates = pd.Series(d["Date"].drop_duplicates().values)
        mult = pd.Series(
            self.calendar_.predict(_calendar_features(unique_dates, self.use_weeks, self.use_holidays)),
            index=unique_dates.values)
        return np.maximum(base * d["Date"].map(mult).values, 0.0)


class GradientBoostingDemandModel:
    """Direct gradient boosting on raw calendar features (no profile structure)."""

    def fit(self, df: pd.DataFrame):
        self.encoder_ = LabelEncoder().fit(df["Station"])
        X = self._features(_with_calendar(df))
        self.model_ = HistGradientBoostingRegressor(
            max_iter=300, learning_rate=0.1, min_samples_leaf=20, random_state=42)
        self.model_.fit(X, df["Entries"].values)
        return self

    def _features(self, d: pd.DataFrame) -> pd.DataFrame:
        return pd.DataFrame({
            "station": self.encoder_.transform(d["Station"]), "hour": d["Hour"].values,
            "day_of_week": d["day_of_week"].values, "month": d["month"].values,
            "is_weekend": d["is_weekend"].values,
            "trend_days": (d["Date"] - EPOCH).dt.days.values,
            "day_of_year": d["Date"].dt.dayofyear.values,
        })

    def predict(self, df: pd.DataFrame) -> np.ndarray:
        return np.maximum(self.model_.predict(self._features(_with_calendar(df))), 0.0)


CANDIDATES = {
    "historical_average_baseline": lambda: HistoricalAverageBaseline(),
    "profile_plus_trend_seasonality": lambda: ProfileCalendarModel(use_weeks=False),
    "profile_plus_week_of_year": lambda: ProfileCalendarModel(use_weeks=True),
    "profile_plus_holiday_calendar": lambda: ProfileCalendarModel(use_weeks=True, use_holidays=True),
    "gradient_boosting_direct": lambda: GradientBoostingDemandModel(),
}


# ---------------------------------------------------------------------------
# Delay-risk model (two stage)
# ---------------------------------------------------------------------------
class DelayRiskModel:
    """P(delay this hour) x expected severity (minutes) if a delay happens."""

    def fit(self, df: pd.DataFrame):
        """df columns: Date, Station, Hour, Entries, has_delay, DelayMinutes."""
        d = _with_calendar(df)
        prof = d.groupby(["Station", "Hour", "day_of_week"])["Entries"].mean().rename("profile_entries")
        self.profile_ = prof.reset_index()
        X = self._features(d)
        self.classifier_ = HistGradientBoostingClassifier(max_depth=4, max_iter=150, random_state=42)
        self.classifier_.fit(X, d["has_delay"])
        pos = d["has_delay"] == 1
        self.regressor_ = HistGradientBoostingRegressor(max_depth=4, max_iter=150, random_state=42)
        self.regressor_.fit(X[pos.values], d.loc[pos, "DelayMinutes"])
        self.mean_severity_ = float(d.loc[pos, "DelayMinutes"].mean())
        return self

    def _features(self, d: pd.DataFrame) -> pd.DataFrame:
        m = d.merge(self.profile_, on=["Station", "Hour", "day_of_week"], how="left")
        cap = m["Station"].map(repo.load_capacity()).fillna(repo.FALLBACK_CAPACITY).values
        profile = m["profile_entries"].fillna(m["profile_entries"].mean()).values
        return pd.DataFrame({
            "profile_congestion": profile / cap, "capacity": cap, "hour": m["Hour"].values,
            "day_of_week": m["day_of_week"].values, "is_weekend": m["is_weekend"].values,
            "month": m["month"].values,
        })

    def predict(self, df: pd.DataFrame) -> pd.DataFrame:
        X = self._features(_with_calendar(df))
        prob = self.classifier_.predict_proba(X)[:, 1]
        severity = np.maximum(self.regressor_.predict(X), 0.0)
        return pd.DataFrame({"probability": prob, "severity": severity, "expected": prob * severity})


def _delay_frame() -> pd.DataFrame:
    df = repo.load_data()[["Date", "Hour", "Station", "Entries"]]
    delays = repo.load_delays()[["Date", "Hour", "Station", "DelayMinutes"]]
    merged = df.merge(delays, on=["Date", "Hour", "Station"], how="left")
    merged["has_delay"] = merged["DelayMinutes"].notna().astype(int)
    merged["DelayMinutes"] = merged["DelayMinutes"].fillna(0.0)
    return merged


# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------
def _vst(x) -> np.ndarray:
    """Anscombe transform: makes Poisson-like counts have ~unit variance."""
    return 2.0 * np.sqrt(np.maximum(np.asarray(x, dtype=float), 0.0) + 0.375)


def _inverse_vst(v) -> np.ndarray:
    return np.maximum((np.asarray(v, dtype=float) / 2.0) ** 2 - 0.375, 0.0)


def _interval(point, q: float):
    """Symmetric interval on the variance-stabilised scale, mapped back to counts."""
    v = _vst(point)
    return _inverse_vst(v - q), _inverse_vst(v + q)


def _evaluate_demand(df: pd.DataFrame) -> dict:
    dev, test = _dev_test_split(df)

    # --- 1. model selection by expanding-window cross-validation ---
    fold_scores = {name: [] for name in CANDIDATES}
    oof = {name: [] for name in CANDIDATES}   # out-of-fold (actual, prediction) pairs
    fold_periods = []
    for train, val in _cv_folds(dev):
        fold_periods.append(_period(val))
        for name, make in CANDIDATES.items():
            pred = make().fit(train).predict(val)
            fold_scores[name].append(round(float(mean_absolute_error(val["Entries"], pred)), 2))
            oof[name].append((val["Entries"].values, pred))
    cv_scores = {
        name: {"mean_mae": round(float(np.mean(v)), 2), "fold_mae": v} for name, v in fold_scores.items()
    }
    best = min(cv_scores, key=lambda n: cv_scores[n]["mean_mae"])

    # --- 2. calibrate prediction intervals + anomaly sigma on out-of-fold residuals ---
    # Only the two most recent folds are used: their models saw the most training data,
    # so they resemble the deployed model. Early folds (trained on a few months) are
    # much noisier and would make every interval needlessly wide.
    y_oof = np.concatenate([y for y, _ in oof[best][-CALIBRATION_FOLDS:]])
    p_oof = np.concatenate([p for _, p in oof[best][-CALIBRATION_FOLDS:]])
    resid = _vst(y_oof) - _vst(p_oof)
    q90 = float(np.quantile(np.abs(resid), 0.90))
    sigma = float(np.std(resid))

    # --- 3. final untouched test: refit on the development period ---
    best_model = CANDIDATES[best]().fit(dev)
    baseline_model = CANDIDATES["historical_average_baseline"]().fit(dev)
    test_pred = best_model.predict(test)
    base_pred = baseline_model.predict(test)
    test_metrics = _metrics(test["Entries"], test_pred)
    base_metrics = _metrics(test["Entries"], base_pred)
    improvement = round((1 - test_metrics["mae"] / max(base_metrics["mae"], 1e-9)) * 100, 1)

    y_test = test["Entries"].values
    lower, upper = _interval(test_pred, q90)
    coverage = float(np.mean((y_test >= lower) & (y_test <= upper)) * 100)

    # --- 4. anomaly detector evaluation on the test period ---
    z = (_vst(y_test) - _vst(test_pred)) / sigma
    false_alarm = float(np.mean(np.abs(z) > ANOMALY_Z) * 100)
    rng = np.random.default_rng(7)
    idx = rng.choice(len(y_test), size=max(1, len(y_test) // 100), replace=False)
    z_inj = (_vst(np.round(y_test[idx] * 1.5)) - _vst(test_pred[idx])) / sigma
    recall_all = float(np.mean(z_inj > ANOMALY_Z) * 100)
    big = test_pred[idx] >= 500
    recall_busy = float(np.mean(z_inj[big] > ANOMALY_Z) * 100) if big.any() else None

    # --- 5. final deployment model: refit on everything ---
    final_model = CANDIDATES[best]().fit(df)

    if improvement > 0:
        note = (f"The selected model '{best}' beats the historical-average baseline by "
                f"{improvement}% MAE on the untouched test period.")
    else:
        note = (f"The historical-average baseline is competitive with '{best}' on this dataset "
                f"({improvement}% MAE vs baseline).")

    report = {
        "periods": {"development": _period(dev), "test": _period(test), "cv_validation_folds": fold_periods},
        "rows": {"development": int(len(dev)), "test": int(len(test))},
        "candidate_cross_validation": cv_scores,
        "selected_model": best,
        "test_metrics_selected": test_metrics,
        "test_metrics_baseline": base_metrics,
        "improvement_over_baseline_mae_pct": improvement,
        "comparison_note": note,
        "prediction_interval": {
            "nominal_coverage_pct": 90, "anscombe_half_width": round(q90, 3),
            "empirical_coverage_on_test_pct": round(coverage, 1),
            "method": "Anscombe-transformed forecast +/- q, mapped back to counts; "
                      "q calibrated on the two most recent cross-validation folds",
        },
        "anomaly_detector": {
            "rule": f"|observed - forecast| > {ANOMALY_Z} sigma", "sigma_scaled": round(sigma, 3),
            "false_alarm_rate_on_test_pct": round(false_alarm, 3),
            "recall_on_injected_50pct_spikes_pct": round(recall_all, 1),
            "recall_on_injected_spikes_busy_hours_pct": None if recall_busy is None else round(recall_busy, 1),
            "note": "Busy-hour recall (forecast >= 500 entries) is the meaningful figure; "
                    "a 50% spike on a 5-passenger overnight hour is statistically undetectable.",
        },
    }
    return {"report": report, "final_model": final_model, "sigma": sigma, "q90": q90}


def _evaluate_delay(df: pd.DataFrame) -> dict:
    dev, test = _dev_test_split(df)
    model = DelayRiskModel().fit(dev)
    pred = model.predict(test)
    y = test["has_delay"].values
    base_rate = float(dev["has_delay"].mean())
    brier = float(brier_score_loss(y, pred["probability"]))
    brier_base = float(brier_score_loss(y, np.full(len(y), base_rate)))
    pos = y == 1
    sev_mae = float(mean_absolute_error(test.loc[pos, "DelayMinutes"], pred.loc[pos, "severity"]))
    sev_mae_base = float(mean_absolute_error(test.loc[pos, "DelayMinutes"],
                                              np.full(pos.sum(), model.mean_severity_)))
    report = {
        "delay_event_rate_pct": round(base_rate * 100, 2),
        "classifier": {
            "algorithm": "HistGradientBoostingClassifier",
            "roc_auc": round(float(roc_auc_score(y, pred["probability"])), 3),
            "roc_auc_random_guess": 0.5,
            "pr_auc": round(float(average_precision_score(y, pred["probability"])), 4),
            "pr_auc_random_guess": round(float(y.mean()), 4),
            "brier_score": round(brier, 5), "brier_score_base_rate_only": round(brier_base, 5),
            "brier_skill_vs_base_rate_pct": round((1 - brier / brier_base) * 100, 2),
            "note": "Accuracy is deliberately not reported: always predicting 'no delay' is "
                    "already ~98% accurate on rare events. Delays are rare and only weakly "
                    "predictable from calendar and crowd patterns, so modest AUC is the "
                    "realistic outcome; the useful output is the relative risk ranking by hour.",
        },
        "severity_regressor": {
            "algorithm": "HistGradientBoostingRegressor",
            "mae_minutes": round(sev_mae, 2), "mae_minutes_predicting_mean": round(sev_mae_base, 2),
            "trained_on_delay_events_only": True,
        },
    }
    return {"report": report, "final_model": DelayRiskModel().fit(df)}


def train_model() -> dict:
    demand_df = repo.load_data()[["Date", "Hour", "Station", "Entries"]]
    demand = _evaluate_demand(demand_df)
    delay = _evaluate_delay(_delay_frame())

    MODEL_DIR.mkdir(exist_ok=True)
    joblib.dump({"model": demand["final_model"], "sigma": demand["sigma"],
                 "q90": demand["q90"]}, DEMAND_MODEL_PATH)
    joblib.dump(delay["final_model"], DELAY_MODEL_PATH)

    metadata = {
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "deployment_note": "Models are evaluated on a chronological split, then refit on all data for serving.",
        "demand": demand["report"],
        "delay": delay["report"],
    }
    METADATA_PATH.write_text(json.dumps(metadata, indent=2))
    with _LOCK:
        _CACHE["models"] = (joblib.load(DEMAND_MODEL_PATH), delay["final_model"])
    return metadata


# ---------------------------------------------------------------------------
# Serving
# ---------------------------------------------------------------------------
_CACHE: dict = {}
_LOCK = threading.RLock()  # requests run in worker threads; load/train the models once


def _models():
    if "models" not in _CACHE:
        with _LOCK:
            if "models" not in _CACHE:
                if not (DEMAND_MODEL_PATH.exists() and DELAY_MODEL_PATH.exists()):
                    train_model()
                else:
                    _CACHE["models"] = (joblib.load(DEMAND_MODEL_PATH), joblib.load(DELAY_MODEL_PATH))
    return _CACHE["models"]


def get_model_metadata() -> dict:
    if not METADATA_PATH.exists():
        return train_model()
    return json.loads(METADATA_PATH.read_text())


def _forecast_frame(station: str, date: str, hours: list[int]) -> list[dict]:
    demand_bundle, delay_model = _models()
    frame = pd.DataFrame({"Date": pd.Timestamp(date), "Station": station, "Hour": hours})
    point = demand_bundle["model"].predict(frame)
    lower, upper = _interval(point, demand_bundle["q90"])
    delay = delay_model.predict(frame)
    capacity = repo.get_capacity(station)
    out = []
    for i, h in enumerate(hours):
        out.append({
            "station": station, "date": date, "hour": int(h),
            "predicted_entries": round(float(point[i]), 1),
            "predicted_entries_90pct_range": [round(float(lower[i]), 1), round(float(upper[i]), 1)],
            "predicted_congestion_pct": round(min(100.0, float(point[i]) / capacity * 100), 1),
            "delay_probability": round(float(delay["probability"].iloc[i]), 4),
            "expected_severity_minutes_if_delayed": round(float(delay["severity"].iloc[i]), 1),
            "expected_delay_minutes": round(float(delay["expected"].iloc[i]), 2),
        })
    return out


def forecast_peak_hours(station: str, date: str) -> list[dict]:
    """24-hour demand + delay-risk forecast for one station and date."""
    return _forecast_frame(station, date, list(range(24)))


def predict_demand(station: str, date: str, hour: int) -> dict:
    f = _forecast_frame(station, date, [hour])[0]
    return {k: f[k] for k in ("station", "date", "hour", "predicted_entries",
                              "predicted_entries_90pct_range", "predicted_congestion_pct")}


def predict_delay(station: str, date: str, hour: int) -> dict:
    f = _forecast_frame(station, date, [hour])[0]
    return {k: f[k] for k in ("station", "date", "hour", "delay_probability",
                              "expected_severity_minutes_if_delayed", "expected_delay_minutes")}


def smart_recommendations(station: str, date: str) -> list[str]:
    recs = []
    base_rate = get_model_metadata()["delay"]["delay_event_rate_pct"] / 100
    risk_threshold = 1.4 * base_rate  # "elevated" = 40% above the network-wide delay rate
    for f in forecast_peak_hours(station, date):
        h, pct = f["hour"], f["predicted_congestion_pct"]
        if pct >= 90:
            recs.append(f"{station} @ {h:02d}:00 - CRITICAL demand forecast ({pct}% of capacity, "
                        f"likely {f['predicted_entries_90pct_range'][0]:.0f}-"
                        f"{f['predicted_entries_90pct_range'][1]:.0f} entries). Increase train frequency.")
        elif pct >= 70:
            recs.append(f"{station} @ {h:02d}:00 - High demand forecast ({pct}%). Add platform staff.")
        if f["delay_probability"] >= risk_threshold:
            recs.append(f"{station} @ {h:02d}:00 - Elevated delay risk ({f['delay_probability'] * 100:.1f}% "
                        f"chance vs {base_rate * 100:.1f}% network average, about {f['expected_severity_minutes_if_delayed']} min if it occurs).")
    if not recs:
        recs.append(f"{station} - no critical congestion or elevated delay risk forecast for {date}.")
    return recs


# ---------------------------------------------------------------------------
# Anomaly detection
# ---------------------------------------------------------------------------
def _score(station: str, date: str, hour: int, observed: float) -> dict:
    bundle, _ = _models()
    frame = pd.DataFrame({"Date": [pd.Timestamp(date)], "Station": [station], "Hour": [hour]})
    expected = float(bundle["model"].predict(frame)[0])
    z = float((_vst(observed) - _vst(expected)) / bundle["sigma"])
    verdict = "SPIKE" if z > ANOMALY_Z else "DROP" if z < -ANOMALY_Z else "NORMAL"
    return {
        "station": station, "date": date, "hour": hour,
        "observed_entries": round(float(observed), 1), "expected_entries": round(expected, 1),
        "z_score": round(float(z), 2), "verdict": verdict,
        "deviation_pct": round((observed - expected) / max(expected, 1.0) * 100, 1),
    }


def score_observation(station: str, date: str, hour: int, observed_entries: float) -> dict:
    """Is this observed passenger count unusual for this station/date/hour?"""
    return _score(station, date, hour, observed_entries)


def detect_anomalies(on_date: str, hour: int) -> dict:
    """Compare every station's recorded entries at date/hour with the model forecast."""
    snapshot = repo.all_stations_snapshot(on_date, hour)
    results = [_score(s["station"], on_date, hour, s["entries"]) for s in snapshot]
    flagged = [r for r in results if r["verdict"] != "NORMAL"]
    return {"date": on_date, "hour": hour, "stations_checked": len(results),
            "anomalies": sorted(flagged, key=lambda r: -abs(r["z_score"]))}
