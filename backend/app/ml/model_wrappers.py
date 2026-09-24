import logging
import os
from datetime import datetime, timedelta

import numpy as np

from app.core.time import utcnow
from app.ml import features as feat
from app.ml import registry

logger = logging.getLogger(__name__)

_KAGGLE_CITIES = {"seoul", "hangzhou", "nyc", "tfl", "beijing"}

_store_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "models_store",
)
_store_dir = os.environ.get("MODELS_STORE_DIR", _store_dir)


def _load_artifact(filename: str):
    try:
        import joblib
    except ImportError:
        logger.warning("joblib not installed; using rule-based fallback")
        return None
    path = os.path.join(_store_dir, filename)
    if not os.path.exists(path):
        logger.warning(f"{filename} not found; using rule-based fallback")
        return None
    try:
        data = joblib.load(path)
        logger.info(f"Loaded ML artifact: {filename}")
        return data
    except Exception as e:
        logger.warning(f"Failed to load {filename} ({e}); using fallback")
        return None


def _city_file(kind: str) -> str:
    """Prefer the per-city artifact (e.g. hangzhou_crowd_model.joblib); fall
    back to the legacy synthetic artifact (crowd_model.joblib). For the crowd
    model the quantile variant (native confidence intervals) wins when present."""
    city = registry.model_city()
    if kind == "crowd":
        quantile_name = f"{city}_crowd_quantile_model.joblib"
        if os.path.exists(os.path.join(_store_dir, quantile_name)):
            return quantile_name
    city_name = f"{city}_{kind}_model.joblib"
    if os.path.exists(os.path.join(_store_dir, city_name)):
        return city_name
    return f"{kind}_model.joblib"


class CrowdModel:
    def __init__(self):
        self.artifact = _load_artifact(_city_file("crowd"))
        self.stations = []
        self.cap_norm_scale = 700.0
        self.trained_on = None
        self.low_model = None
        self.high_model = None
        if isinstance(self.artifact, dict):
            self.stations = list(self.artifact.get("stations") or [])
            self.cap_norm_scale = float(self.artifact.get("cap_norm_scale", 700.0))
            self.trained_on = self.artifact.get("trained_on")
            if self.artifact.get("kind") == "quantile":
                self.low_model = self.artifact.get("low")
                self.high_model = self.artifact.get("high")
        self.residual_std = 0.05 if not isinstance(self.artifact, dict) else float(self.artifact.get("residual_std", 0.05))

    @property
    def is_loaded(self) -> bool:
        return self.artifact is not None

    @property
    def is_quantile(self) -> bool:
        return self.low_model is not None and self.high_model is not None

    @property
    def is_kaggle(self) -> bool:
        return bool(self.stations) and self.trained_on in _KAGGLE_CITIES

    def _feature_rows(
        self, hours: list[int], weekday, station: dict | None = None
    ) -> np.ndarray:
        # `weekday` may be a single int (uniform) or a per-row sequence so
        # multi-day forecast windows resolve the correct day-of-week per hour.
        sid = (station or {}).get("id")
        cap = (station or {}).get("capacity_per_hour")
        wd_list = (
            list(weekday)
            if isinstance(weekday, (list, tuple, np.ndarray))
            else [weekday] * len(hours)
        )
        if self.is_kaggle:
            code = registry.city_station_code(sid)
            return np.array([
                feat.kaggle_row_features(h, wd, code, cap, self.stations, self.cap_norm_scale)
                for h, wd in zip(hours, wd_list)
            ])
        return np.array([feat.row_features(h, wd, sid, cap) for h, wd in zip(hours, wd_list)])

    def _predict_raw(self, X: np.ndarray, hours: list[int], weekday, capacity_per_hour: float | None = None) -> np.ndarray:
        if self.artifact is not None:
            try:
                model = self.artifact["model"] if isinstance(self.artifact, dict) else self.artifact
                return np.asarray(model.predict(X), dtype=float)
            except Exception as e:
                logger.warning(f"crowd model predict failed ({e}); using baseline")
        cap_ratio = (capacity_per_hour or 520.0) / 520.0
        if isinstance(weekday, (list, tuple, np.ndarray)):
            return np.array([
                feat.station_baseline_occupancy_pct(h) * (feat.WEEKEND_FACTOR if wd >= 5 else 1.0)
                * cap_ratio
                for h, wd in zip(hours, list(weekday))
            ])
        return np.array([
            feat.station_baseline_occupancy_pct(h) * (feat.WEEKEND_FACTOR if weekday >= 5 else 1.0)
            * cap_ratio
            for h in hours
        ])

    def _predict_bounds(
        self, X: np.ndarray, hours: list[int], weekday, capacity_per_hour: float | None = None
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Return (center, lower, upper) occupancy-fraction predictions.
        Quantile artifacts provide native bounds; others fall back to a
        symmetric residual_std band."""
        if self.is_quantile:
            try:
                center = np.asarray(self.artifact["model"].predict(X), dtype=float)
                low = np.asarray(self.low_model.predict(X), dtype=float)
                high = np.asarray(self.high_model.predict(X), dtype=float)
                low = np.minimum(low, center)
                high = np.maximum(high, center)
                return center, low, high
            except Exception as e:
                logger.warning(f"quantile crowd predict failed ({e}); using residual band")
        pred = self._predict_raw(X, hours, weekday, capacity_per_hour)
        return pred, pred - self.residual_std, pred + self.residual_std

    def predict_hourly(
        self,
        base_hour: int,
        hours_ahead: int = 12,
        weekday: int | None = None,
        station: dict | None = None,
    ) -> list[dict]:
        now = utcnow()
        if weekday is None:
            weekday = now.weekday()
        hours = [(base_hour + h) % 24 for h in range(hours_ahead)]
        cap = (station or {}).get("capacity_per_hour")
        X = self._feature_rows(hours, weekday, station)
        center, low, high = self._predict_bounds(X, hours, weekday, cap)

        results = []
        for i, c in enumerate(center):
            pct = float(np.clip(c, 0.05, 1.2)) * 100.0
            ts = now + timedelta(hours=i)
            lower = max(0.0, float(np.clip(low[i], 0.05, 1.2)) * 100.0)
            upper = min(100.0, float(np.clip(high[i], 0.05, 1.2)) * 100.0)
            results.append({
                "hour": hours[i],
                "predicted_occupancy_pct": round(pct, 2),
                "lower": round(lower, 2),
                "upper": round(upper, 2),
                "congestion_level": feat.congestion_from_pct(pct / 100.0),
                "timestamp": ts.isoformat() + "Z",
            })
        return results

    def predict_period(
        self,
        start_dt: datetime,
        hours_ahead: int = 12,
        station: dict | None = None,
    ) -> list[dict]:
        """Forecast crowd occupancy for an arbitrary window starting at
        `start_dt` (any date/time). day-of-week is resolved per hour so the
        window can span multiple days (weekday vs weekend are handled
        correctly by the trained models)."""
        start_dt = start_dt.replace(minute=0, second=0, microsecond=0)
        dts = [start_dt + timedelta(hours=i) for i in range(hours_ahead)]
        hours = [d.hour for d in dts]
        weekdays = [d.weekday() for d in dts]
        cap = (station or {}).get("capacity_per_hour")
        X = self._feature_rows(hours, weekdays, station)
        center, low, high = self._predict_bounds(X, hours, weekdays, cap)

        results = []
        for i, c in enumerate(center):
            pct = float(np.clip(c, 0.05, 1.2)) * 100.0
            lower = max(0.0, float(np.clip(low[i], 0.05, 1.2)) * 100.0)
            upper = min(100.0, float(np.clip(high[i], 0.05, 1.2)) * 100.0)
            results.append({
                "hour": hours[i],
                "date": dts[i].strftime("%Y-%m-%d"),
                "predicted_occupancy_pct": round(pct, 2),
                "lower": round(lower, 2),
                "upper": round(upper, 2),
                "congestion_level": feat.congestion_from_pct(pct / 100.0),
                "timestamp": dts[i].isoformat() + "Z",
            })
        return results


class DemandForecaster:
    def __init__(self):
        self.artifact = _load_artifact(_city_file("demand"))
        self.stations = []
        self.cap_norm_scale = 700.0
        self.trained_on = None
        if isinstance(self.artifact, dict):
            self.stations = list(self.artifact.get("stations") or [])
            self.cap_norm_scale = float(self.artifact.get("cap_norm_scale", 700.0))
            self.trained_on = self.artifact.get("trained_on")

    @property
    def is_loaded(self) -> bool:
        return self.artifact is not None

    @property
    def is_kaggle(self) -> bool:
        return bool(self.stations) and self.trained_on in _KAGGLE_CITIES

    def _feature_rows(
        self, hours: list[int], weekday, station: dict | None = None
    ) -> np.ndarray:
        sid = (station or {}).get("id")
        cap = (station or {}).get("capacity_per_hour")
        wd_list = (
            list(weekday)
            if isinstance(weekday, (list, tuple, np.ndarray))
            else [weekday] * len(hours)
        )
        if self.is_kaggle:
            code = registry.city_station_code(sid)
            return np.array([
                feat.kaggle_row_features(h, wd, code, cap, self.stations, self.cap_norm_scale)
                for h, wd in zip(hours, wd_list)
            ])
        return np.array([feat.row_features(h, wd, sid, cap) for h, wd in zip(hours, wd_list)])

    def _predict(self, X: np.ndarray, hours: list[int], capacity_per_hour: float | None = None) -> np.ndarray:
        if self.artifact is not None:
            try:
                model = self.artifact["model"] if isinstance(self.artifact, dict) else self.artifact
                return np.asarray(model.predict(X), dtype=float)
            except Exception as e:
                logger.warning(f"demand model predict failed ({e}); using baseline")
        cap_ratio = (capacity_per_hour or 520.0) / 520.0
        return np.array([
            feat.demand_base_entries(h) * cap_ratio
            for h in hours
        ])

    def forecast_hourly(
        self,
        base_hour: int,
        hours_ahead: int = 12,
        weekday: int | None = None,
        station: dict | None = None,
    ) -> list[dict]:
        now = utcnow()
        if weekday is None:
            weekday = now.weekday()
        hours = [(base_hour + h) % 24 for h in range(hours_ahead)]
        cap = (station or {}).get("capacity_per_hour")
        X = self._feature_rows(hours, weekday, station)
        entries_pred = self._predict(X, hours, cap)

        results = []
        for i, e in enumerate(entries_pred):
            hr = hours[i]
            factor = 1.0 if self.is_kaggle else (1.5 if weekday < 5 else 0.75)
            entry_val = max(0, int(round(float(e) * factor)))
            if self.is_kaggle:
                exit_val = max(0, int(round(entry_val * 0.85)))
            else:
                exit_val = max(0, int(round(entry_val * feat.station_baseline_occupancy_pct(hr) * 0.9)))
            peak_prob = min(1.0, feat.BASELINE_OCCUPANCY[hr] + (0.15 if hr in feat.PEAK_MULTIPLIER else 0.0))
            results.append({
                "hour": hr,
                "predicted_entries": entry_val,
                "predicted_exits": exit_val,
                "peak_probability": round(peak_prob, 3),
            })
        return results

    def forecast_period(
        self,
        start_dt: datetime,
        hours_ahead: int = 12,
        station: dict | None = None,
    ) -> list[dict]:
        """Forecast gate demand for an arbitrary window starting at `start_dt`.
        Day-of-week is resolved per hour (multi-day windows treat weekday vs
        weekend correctly)."""
        start_dt = start_dt.replace(minute=0, second=0, microsecond=0)
        dts = [start_dt + timedelta(hours=i) for i in range(hours_ahead)]
        hours = [d.hour for d in dts]
        weekdays = [d.weekday() for d in dts]
        cap = (station or {}).get("capacity_per_hour")
        X = self._feature_rows(hours, weekdays, station)
        entries_pred = self._predict(X, hours, cap)

        results = []
        for i, e in enumerate(entries_pred):
            hr = hours[i]
            wd = weekdays[i]
            factor = 1.0 if self.is_kaggle else (1.5 if wd < 5 else 0.75)
            entry_val = max(0, int(round(float(e) * factor)))
            if self.is_kaggle:
                exit_val = max(0, int(round(entry_val * 0.85)))
            else:
                exit_val = max(0, int(round(entry_val * feat.station_baseline_occupancy_pct(hr) * 0.9)))
            peak_prob = min(1.0, feat.BASELINE_OCCUPANCY[hr] + (0.15 if hr in feat.PEAK_MULTIPLIER else 0.0))
            results.append({
                "hour": hr,
                "date": dts[i].strftime("%Y-%m-%d"),
                "predicted_entries": entry_val,
                "predicted_exits": exit_val,
                "peak_probability": round(peak_prob, 3),
                "timestamp": dts[i].isoformat() + "Z",
            })
        return results


class DelayForecaster:
    """NJ Transit delay model (line/schedule aware). No synthetic fallback:
    if the classifier/regressor artifacts are missing, predict() raises."""

    _CLS_FILE = "delay_classifier.joblib"
    _REG_FILE = "delay_regressor.joblib"

    def __init__(self):
        self.artifact = _load_artifact(self._CLS_FILE)
        self.regressor = _load_artifact(self._REG_FILE)
        self.feature_names: list[str] = []
        self.classes: list[str] = []
        self.line_names: list[str] = []
        self.type_names: list[str] = []
        self.from_ids: list[str] = []
        self.to_ids: list[str] = []
        self.trained_on = None
        if isinstance(self.artifact, dict):
            self.feature_names = list(self.artifact.get("feature_names") or [])
            self.classes = list(self.artifact.get("classes") or [])
            self.line_names = list(self.artifact.get("line_names") or [])
            self.type_names = list(self.artifact.get("type_names") or [])
            self.from_ids = list(self.artifact.get("from_ids") or [])
            self.to_ids = list(self.artifact.get("to_ids") or [])
            self.trained_on = self.artifact.get("trained_on")

    @property
    def is_loaded(self) -> bool:
        return isinstance(self.artifact, dict) and isinstance(self.regressor, dict)

    def _row(
        self,
        hour: int,
        weekday: int,
        sched_minutes: float,
        stop_sequence: float,
        line: str,
        from_station: str,
        to_station: str,
        train_type: str,
    ) -> np.ndarray:
        from_map = {v: i for i, v in enumerate(self.from_ids)}
        to_map = {v: i for i, v in enumerate(self.to_ids)}
        mins = float(sched_minutes)
        line_oh = np.zeros(len(self.line_names), dtype=np.float32)
        if line in self.line_names:
            line_oh[self.line_names.index(line)] = 1.0
        type_oh = np.zeros(len(self.type_names), dtype=np.float32)
        if train_type in self.type_names:
            type_oh[self.type_names.index(train_type)] = 1.0
        row = np.hstack([
            feat.hour_to_features(int(hour) % 24, int(weekday) % 7),
            np.array([
                np.sin(2 * np.pi * mins / 1440),
                np.cos(2 * np.pi * mins / 1440),
                min(max(float(stop_sequence) / 50.0, 0.0), 2.0),
                float(from_map.get(str(from_station), -1)),
                float(to_map.get(str(to_station), -1)),
            ], dtype=np.float32),
            line_oh,
            type_oh,
        ])
        return row.astype(np.float32)

    def predict(
        self,
        hour: int,
        weekday: int,
        sched_minutes: float,
        stop_sequence: float,
        line: str,
        from_station: str | None,
        to_station: str | None,
        train_type: str = "NJ Transit",
    ) -> dict:
        if not self.is_loaded:
            raise RuntimeError("NJ delay model not available")
        X = self._row(hour, weekday, sched_minutes, stop_sequence,
                      line, from_station or "", to_station or "", train_type).reshape(1, -1)
        proba = np.asarray(self.artifact["model"].predict_proba(X))[0]
        pred_min = float(np.clip(np.asarray(self.regressor["model"].predict(X))[0], 0.0, None))
        idx = int(np.argmax(proba))
        return {
            "line": line,
            "from_station": from_station or "",
            "to_station": to_station or "",
            "delay_bucket": self.classes[idx],
            "probabilities": {str(c): round(float(p), 4) for c, p in zip(self.classes, proba)},
            "predicted_delay_minutes": round(pred_min, 1),
        }


_crowd_model: CrowdModel | None = None
_demand_model: DemandForecaster | None = None
_delay_model: DelayForecaster | None = None


def load_models() -> None:
    global _crowd_model, _demand_model, _delay_model
    _crowd_model = CrowdModel()
    _demand_model = DemandForecaster()
    _delay_model = DelayForecaster()


def get_crowd_model() -> CrowdModel:
    global _crowd_model
    if _crowd_model is None:
        load_models()
    return _crowd_model


def get_demand_model() -> DemandForecaster:
    global _demand_model
    if _demand_model is None:
        load_models()
    return _demand_model


def get_delay_model() -> DelayForecaster:
    global _delay_model
    if _delay_model is None:
        load_models()
    return _delay_model