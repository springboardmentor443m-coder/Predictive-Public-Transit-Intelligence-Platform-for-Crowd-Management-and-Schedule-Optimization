"""Application configuration.

The `ENVIRONMENT` switch exists so a development convenience cannot quietly
become a production vulnerability. The shipped default JWT secret is committed
to the repository, so an operator who copies `.env.example` and deploys without
editing it would otherwise mint tokens that anyone holding the repo can forge.
Rather than only logging a warning, production refuses to start.
"""

import logging
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

#: Committed in the repository, therefore public. Never valid in production.
INSECURE_DEV_SECRET = "metroflow-dev-secret-change-in-production"

PRODUCTION_ENVIRONMENTS = {"production", "prod"}


class Settings(BaseSettings):
    APP_NAME: str = "MetroFlow API"
    VERSION: str = "1.0.0"
    #: development | staging | production. Gates the safety checks below.
    ENVIRONMENT: str = "development"
    DATABASE_URL: str = "postgresql+psycopg2://metroflow:metroflow@localhost:5432/metroflow"
    MONGODB_URL: str = "mongodb://localhost:27017"
    REDIS_URL: str = "redis://localhost:6379/0"
    JWT_SECRET_KEY: str = INSECURE_DEV_SECRET
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 720
    CORS_ORIGINS: str = "http://localhost:3000"
    #: Write demo users and generated history on startup. Must be false in prod.
    SEED_DEMO_DATA: bool = True

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.strip().lower() in PRODUCTION_ENVIRONMENTS

    def assert_production_safe(self) -> None:
        """Fail fast on settings that are unsafe outside development."""
        if not self.is_production:
            return

        problems: list[str] = []
        if self.JWT_SECRET_KEY == INSECURE_DEV_SECRET:
            problems.append(
                "JWT_SECRET_KEY is still the committed development default; anyone with the "
                "repository can mint valid tokens. Set a strong random value."
            )
        elif len(self.JWT_SECRET_KEY) < 32:
            problems.append("JWT_SECRET_KEY is shorter than 32 characters.")
        if self.SEED_DEMO_DATA:
            problems.append(
                "SEED_DEMO_DATA is enabled, which creates shared demo accounts with known "
                "passwords (admin@metroflow.io / Admin@123). Set SEED_DEMO_DATA=false."
            )
        if "*" in self.cors_origin_list:
            problems.append("CORS_ORIGINS contains '*'; restrict it to the real frontend origin.")

        if problems:
            # Refusing to start is the point: a warning would scroll past and the
            # deployment would look healthy.
            raise RuntimeError(
                "Refusing to start in production with unsafe configuration:\n  - "
                + "\n  - ".join(problems)
            )
        logger.info("Production configuration safety checks passed")


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    s.assert_production_safe()
    return s


settings = get_settings()
