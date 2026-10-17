from typing import List, Union

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "MetroFlow Intelligent Metro Operations"
    API_V1_STR: str = "/api/v1"

    # JWT & Security
    SECRET_KEY: str = "super-secret-key-change-in-production-metroflow-2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    # ============================================================
    # DATABASE
    # ============================================================
    # Local development: SQLite
    DATABASE_URL: Union[str, None] = "sqlite:///./metroflow.db"

    # PostgreSQL settings retained for future deployment
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: str = "5432"
    POSTGRES_USER: str = "metroflow_user"
    POSTGRES_PASSWORD: str = "metroflow_password"
    POSTGRES_DB: str = "metroflow_db"

    # Initial Admin Setup
    INITIAL_ADMIN_EMAIL: str = "admin@metroflow.io"
    INITIAL_ADMIN_PASSWORD: str = "AdminPassword123!"
    INITIAL_ADMIN_NAME: str = "System Admin"

    # CORS — includes localhost, 127.0.0.1, and local network IP ranges
    # When Vite runs with host:true it binds to 0.0.0.0, so LAN access goes
    # through the real NIC IP (e.g. 10.x.x.x / 192.168.x.x). Add those here.
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        # LAN/network IP access (Vite host:true)
        "http://10.28.11.76:5173",
        "http://10.28.11.76:3000",
        # Generic 192.168.x.x range (common home/office networks)
        "http://192.168.1.1:5173",
    ]

    # Live Data Provider
    LIVE_DATA_PROVIDER_TYPE: str = "GTFS_RT"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @property
    def sqlalchemy_database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL

        return (
            f"postgresql://{self.POSTGRES_USER}:"
            f"{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_SERVER}:"
            f"{self.POSTGRES_PORT}/"
            f"{self.POSTGRES_DB}"
        )


settings = Settings()