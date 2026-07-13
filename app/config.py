"""
Centralized application configuration.

All environment-driven settings are read here through a single Pydantic
``Settings`` object instead of scattered ``os.getenv`` calls. Import
``get_settings()`` wherever configuration is needed.
"""

from functools import lru_cache
from typing import List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings, populated from the process environment.

    Unknown environment variables are ignored so the same environment can be
    shared with other services (web, mcp) without validation errors.
    """

    model_config = SettingsConfigDict(extra='ignore', case_sensitive=False)

    env: str = 'local'
    lz: Optional[str] = None
    log_level: str = 'INFO'

    # --- Database ---
    database_url: Optional[str] = None
    postgres_user: Optional[str] = None
    postgres_password: Optional[str] = None
    postgres_host: Optional[str] = None
    postgres_connection_port: str = '5432'
    postgres_db: str = 'phoenix'

    # --- Auth ---
    jwt_secret_key: Optional[str] = None
    access_token_expire_minutes: int = 30
    google_client_id: Optional[str] = None

    # --- Observability ---
    loki_url: Optional[str] = None

    # --- CORS (comma-separated origins) ---
    cors_origins: str = 'http://localhost:3000'

    # --- External APIs (movies search proxy) ---
    omdb_api_key: Optional[str] = None
    tmdb_api_key: Optional[str] = None

    # --- External APIs (games search proxy — IGDB via Twitch OAuth) ---
    twitch_client_id: Optional[str] = None
    twitch_client_secret: Optional[str] = None

    @property
    def sqlalchemy_database_url(self) -> str:
        """
        Resolve the SQLAlchemy connection URL.

        ``DATABASE_URL`` wins when set; otherwise local uses SQLite and every
        other environment builds a PostgreSQL URL from the discrete parts.
        """
        if self.database_url:
            return self.database_url
        if self.env == 'local':
            return 'sqlite:///./aleonard-api-local.db'
        return (
            f'postgresql://{self.postgres_user}:{self.postgres_password}'
            f'@{self.postgres_host}:{self.postgres_connection_port}/{self.postgres_db}'
        )

    @property
    def cors_origin_list(self) -> List[str]:
        """Return CORS origins as a list."""
        return [o.strip() for o in self.cors_origins.split(',') if o.strip()]

    @property
    def is_local(self) -> bool:
        """True for the local/SQLite developer environment."""
        return self.env == 'local'

    @property
    def is_ci(self) -> bool:
        """True when running inside CI (GitHub Actions)."""
        return self.env == 'github'


@lru_cache
def get_settings() -> Settings:
    """Return a cached ``Settings`` instance."""
    return Settings()
