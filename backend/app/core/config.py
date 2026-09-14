from pathlib import Path
from pydantic_settings import BaseSettings

ROOT = Path(__file__).resolve().parents[3]  # repo root
BACKEND = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "MetroFlow AI Platform"
    secret_key: str = "metroflow-super-secret-change-in-prod"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 12
    database_url: str = f"sqlite:///{(BACKEND / 'metroflow.db').as_posix()}"
    model_path: str = str((BACKEND / "app" / "ml" / "model.pkl").as_posix())
    data_path: str = str((ROOT / "data" / "nyc_subway_sample.csv").as_posix())

    # Congestion thresholds (passengers / hour in station)
    level_low: int = 800
    level_medium: int = 2000
    level_high: int = 4000

    class Config:
        env_file = ".env"


settings = Settings()
