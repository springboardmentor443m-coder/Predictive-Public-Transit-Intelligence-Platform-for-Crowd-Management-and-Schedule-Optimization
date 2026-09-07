import logging
import os
from datetime import datetime, timedelta

import numpy as np

from app.ml import features as feat

logger = logging.getLogger(__name__)

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


class CrowdModel:
    def __init__(self):
        self.artifact = _load_artifact("crowd_model.joblib")
        self.residual_std = 0.05 if not isinstance(self.artifact, dict) else float(self.artifact.get("residual_std", 0.05))

    @property
    def is_loaded(self) -> bool:
        return self.artifact is not None

    def _predict_raw(self, X: np.ndarray, hours: list[int], weekday: int, capacity_per_hour: float | None = None) -> np.ndarray:
        if self.artifact is not None:
            try:
                model = self.artifact["model"] if isinstance(self.artifact, dict) else self.artifact
                return np.asarray(model.predict(X), dtype=float)
            except Exception as e:
                logger.warning(f"crowd model predict failed ({e}); using baseline")
        cap_ratio = (capacity_per_hour or 520.0) / 520.0
        return np.array([
            feat.station_baseline_occupancy_pct(h) * (feat.WEEKEND_FACTOR if weekday >= 5 else 1.0)
            * cap_ratio
            for h in hours
        ])

    def predict_hourly(
        self,
        base_hour: int,
        hours_ahead: int = 12,
        weekday: int | None = None,
        station: dict | None = None,
    ) -> list[dict]:
        now = datetime.utcnow()
        if weekday is None:
            weekday = now.weekday()
        hours = [(base_hour + h) % 24 for h in range(hours_ahead)]
        sid = (station or {}).get("id")
        cap = (station or {}).get("capacity_per_hour")
        X = np.array([feat.row_features(h, weekday, sid, cap) for h in hours])
        preds = self._predict_raw(X, hours, weekday, cap)

        results = []
        for i, p in enumerate(preds):
            pct = float(np.clip(p, 0.05, 1.2)) * 100.0
            ts = now + timedelta(hours=i)
            lower = max(0.0, pct - self.residual_std * 100)
            upper = min(100.0, pct + self.residual_std * 100)
            results.append({
                "hour": hours[i],
                "predicted_occupancy_pct": round(pct, 2),
                "lower": round(lower, 2),
                "upper": round(upper, 2),
                "congestion_level": feat.congestion_from_pct(pct / 100.0),
                "timestamp": ts.isoformat() + "Z",
            })
        return results


class DemandForecaster:
    def __init__(self):
        self.artifact = _load_artifact("demand_model.joblib")

    @property
    def is_loaded(self) -> bool:
        return self.artifact is not None

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
        now = datetime.utcnow()
        if weekday is None:
            weekday = now.weekday()
        hours = [(base_hour + h) % 24 for h in range(hours_ahead)]
        sid = (station or {}).get("id")
        cap = (station or {}).get("capacity_per_hour")
        X = np.array([feat.row_features(h, weekday, sid, cap) for h in hours])
        entries_pred = self._predict(X, hours, cap)

        results = []
        for i, e in enumerate(entries_pred):
            hr = hours[i]
            factor = 1.5 if weekday < 5 else 0.75
            entry_val = max(0, int(round(float(e) * factor)))
            exit_val = max(0, int(round(entry_val * feat.station_baseline_occupancy_pct(hr) * 0.9)))
            peak_prob = min(1.0, feat.BASELINE_OCCUPANCY[hr] + (0.15 if hr in feat.PEAK_MULTIPLIER else 0.0))
            results.append({
                "hour": hr,
                "predicted_entries": entry_val,
                "predicted_exits": exit_val,
                "peak_probability": round(peak_prob, 3),
            })
        return results


_crowd_model: CrowdModel | None = None
_demand_model: DemandForecaster | None = None


def load_models() -> None:
    global _crowd_model, _demand_model
    _crowd_model = CrowdModel()
    _demand_model = DemandForecaster()


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
