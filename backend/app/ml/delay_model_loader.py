import os
import joblib
from pathlib import Path
from typing import Tuple, Any, Optional
from datetime import datetime
import pandas as pd


def get_season_from_month(month: int) -> str:
    """Helper to derive season label from month (Northern Hemisphere / Seoul)."""
    if month in (12, 1, 2):
        return "Winter"
    elif month in (3, 4, 5):
        return "Spring"
    elif month in (6, 7, 8):
        return "Summer"
    else:
        return "Autumn"


class DelayPredictionModel:
    """
    Singleton ML Model Loader that encapsulates the trained Random Forest Delay Classifier
    and corresponding categorical label encoders (le_season, le_weather).

    Delay model trained on synthetic data anchored to real crowd patterns — ROC-AUC 0.7322.
    Not trained on real-world delay records.
    """
    _instance: Optional["DelayPredictionModel"] = None

    def __init__(
        self,
        model_path: Optional[str] = None,
        season_encoder_path: Optional[str] = None,
        weather_encoder_path: Optional[str] = None,
    ):
        self.model: Any = None
        self.le_season: Any = None
        self.le_weather: Any = None

        self.model_path = model_path or os.getenv("DELAY_MODEL_PATH", "delay_prediction_rf_v2.pkl")
        self.season_encoder_path = season_encoder_path or os.getenv("LE_SEASON_PATH", "le_season.pkl")
        self.weather_encoder_path = weather_encoder_path or os.getenv("LE_WEATHER_PATH", "le_weather.pkl")

        self.is_loaded: bool = False
        self._load_attempted: bool = False

    def _ensure_loaded(self) -> None:
        if not self._load_attempted:
            self.load_model()
            self._load_attempted = True

    @classmethod
    def get_instance(cls) -> "DelayPredictionModel":
        if cls._instance is None:
            cls._instance = DelayPredictionModel()
        return cls._instance

    def _find_file(self, filename: str) -> Optional[Path]:
        possible_paths = [
            Path(filename),
            Path(__file__).resolve().parent.parent.parent.parent / filename,
            Path(__file__).resolve().parent.parent.parent / filename,
            Path(__file__).resolve().parent / filename,
        ]
        for p in possible_paths:
            if p.exists() and p.is_file():
                return p
        return None

    def load_model(self) -> None:
        """
        Loads delay_prediction_rf_v2.pkl, le_season.pkl, and le_weather.pkl into memory.
        """
        m_path = self._find_file(self.model_path)
        s_path = self._find_file(self.season_encoder_path)
        w_path = self._find_file(self.weather_encoder_path)

        if m_path and s_path and w_path:
            try:
                print(f"[Delay ML Loader] Loading delay model artifacts from {m_path.parent}...")
                self.model = joblib.load(m_path)
                self.le_season = joblib.load(s_path)
                self.le_weather = joblib.load(w_path)
                self.is_loaded = True
                print("[Delay ML Loader] Delay prediction model and encoders successfully loaded into memory.")
            except Exception as e:
                print(f"[Delay ML Loader] Note: Could not load pickled delay model artifacts ({e}). Using statistical fallback.")
                self.model = None
                self.le_season = None
                self.le_weather = None
                self.is_loaded = False
        else:
            print(f"[Delay ML Loader] Delay model artifacts not found at expected paths. Using statistical fallback.")
            self.model = None
            self.le_season = None
            self.le_weather = None
            self.is_loaded = False

    def predict(
        self,
        station_code: str,
        line_num: int,
        timestamp: datetime,
        latitude: float = 37.55,
        longitude: float = 126.98,
        season: Optional[str] = None,
        weather_condition: str = "Clear",
        temperature_C: float = 15.0,
        precipitation_mm: float = 0.0,
        real_flow_pattern_ref: float = 50.0,
        is_holiday: int = 0,
    ) -> Tuple[int, float]:
        """
        Predicts delay likelihood and probability.
        
        Delay model trained on synthetic data anchored to real crowd patterns — ROC-AUC 0.7322.
        Not trained on real-world delay records.

        Input features (exact order):
          [station_code, line_num, hour, day_of_week, is_weekend, is_holiday,
           season, weather_condition, temperature_C, precipitation_mm,
           real_flow_pattern_ref, latitude, longitude]
        
        Returns:
          (has_delay: int (0 or 1), delay_probability: float (0.0 to 1.0))
        """
        self._ensure_loaded()

        try:
            code_num = int(station_code)
        except ValueError:
            code_num = hash(station_code) % 1000

        hour = timestamp.hour
        day_of_week = timestamp.weekday()  # 0=Monday, 6=Sunday
        is_weekend = int(day_of_week >= 5)

        if not season:
            season = get_season_from_month(timestamp.month)

        # 1. Primary path: Model inference via loaded artifacts
        if self.is_loaded and self.model is not None and self.le_season is not None and self.le_weather is not None:
            try:
                # Encode categorical features with safe fallbacks
                if season in self.le_season.classes_:
                    encoded_season = int(self.le_season.transform([season])[0])
                else:
                    encoded_season = 0

                normalized_weather = weather_condition.capitalize()
                if normalized_weather in self.le_weather.classes_:
                    encoded_weather = int(self.le_weather.transform([normalized_weather])[0])
                else:
                    # Default to 'Clear' if unknown
                    encoded_weather = int(self.le_weather.transform(["Clear"])[0])

                features_df = pd.DataFrame([{
                    "station_code": code_num,
                    "line_num": line_num,
                    "hour": hour,
                    "day_of_week": day_of_week,
                    "is_weekend": is_weekend,
                    "is_holiday": int(is_holiday),
                    "season": encoded_season,
                    "weather_condition": encoded_weather,
                    "temperature_C": float(temperature_C),
                    "precipitation_mm": float(precipitation_mm),
                    "real_flow_pattern_ref": float(real_flow_pattern_ref),
                    "latitude": float(latitude),
                    "longitude": float(longitude),
                }])

                has_delay = int(self.model.predict(features_df)[0])
                proba = self.model.predict_proba(features_df)[0]
                # Index 1 is probability of delay (class 1)
                delay_probability = float(proba[1]) if len(proba) > 1 else float(has_delay)

                return has_delay, round(delay_probability, 4)
            except Exception as e:
                print(f"[Delay ML Loader] Inference error on model artifact ({e}), falling back to statistical estimation.")

        # 2. Statistical fallback anchored to crowd flow & weather
        return self._predict_fallback(
            real_flow_pattern_ref=real_flow_pattern_ref,
            hour=hour,
            is_weekend=bool(is_weekend),
            weather_condition=weather_condition,
            precipitation_mm=precipitation_mm,
        )

    def _predict_fallback(
        self,
        real_flow_pattern_ref: float,
        hour: int,
        is_weekend: bool,
        weather_condition: str,
        precipitation_mm: float,
    ) -> Tuple[int, float]:
        """
        Statistical estimation fallback anchored to crowd pattern and weather severity.
        """
        # Baseline delay probability ~15%
        base_prob = 0.15

        # Crowd density influence (0-100 density contributes up to +0.35)
        crowd_factor = (min(100.0, max(0.0, real_flow_pattern_ref)) / 100.0) * 0.35

        # Peak hours influence
        peak_factor = 0.10 if (7 <= hour <= 9 or 17 <= hour <= 19) else 0.0

        # Weather factor
        weather_factor = 0.0
        w_lower = weather_condition.lower()
        if "storm" in w_lower or precipitation_mm > 15.0:
            weather_factor = 0.25
        elif "rain" in w_lower or "snow" in w_lower or precipitation_mm > 0.0:
            weather_factor = 0.15
        elif "cloud" in w_lower:
            weather_factor = 0.05

        total_prob = min(0.95, max(0.05, base_prob + crowd_factor + peak_factor + weather_factor))
        has_delay = 1 if total_prob >= 0.50 else 0
        return has_delay, round(total_prob, 4)


delay_ml_model = DelayPredictionModel.get_instance()
