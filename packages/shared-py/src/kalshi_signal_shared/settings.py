from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "kalshi-signal-desk"
    app_env: str = "development"
    app_debug: bool = True
    database_url: str = "postgresql+asyncpg://kalshi:kalshi@postgres:5432/kalshi"
    redis_url: str = "redis://redis:6379/0"
    sentry_dsn: str | None = None
    kalshi_env: str = "demo"
    kalshi_api_key_id: str | None = None
    kalshi_private_key_pem: str | None = None
    kalshi_private_key_path: str | None = None
    kalshi_api_base_url: str | None = None
    kalshi_ws_url: str | None = None
    postgres_url: str | None = None
