from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "MetroFlow API"
    VERSION: str = "1.0.0"
    DATABASE_URL: str = "postgresql+psycopg2://metroflow:metroflow@localhost:5432/metroflow"
    MONGODB_URL: str = "mongodb://localhost:27017"
    REDIS_URL: str = "redis://localhost:6379/0"
    JWT_SECRET_KEY: str = "metroflow-dev-secret-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 720
    CORS_ORIGINS: str = "http://localhost:3000"

    class Config:
        env_file = ".env"
        extra = "ignore"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
