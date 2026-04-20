from pydantic_settings import BaseSettings, SettingsConfigDict


class PlatformSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "kalshi-market-intelligence"
    app_env: str = "development"
    app_debug: bool = False
    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_db: str = "kalshi"
    postgres_user: str = "kalshi"
    postgres_password: str = "kalshi"
    database_url: str = "sqlite+aiosqlite:///./data/kalshi_platform.db"
    database_url_sync: str = "sqlite:///./data/kalshi_platform.db"
    redis_url: str = "redis://redis:6379/0"
    kalshi_api_url: str | None = None
    kalshi_env: str = "demo"
    kalshi_api_key_id: str | None = None
    kalshi_private_key_path: str | None = None
    kalshi_request_timeout_seconds: float = 10.0
    kalshi_enable_trading: bool = False
    sportsbook_odds_api_url: str | None = None
    polymarket_api_url: str | None = None
    metaculus_api_url: str | None = None
    manifold_api_url: str | None = None
    news_api_url: str | None = None
    news_api_key: str | None = None
    pushover_api_url: str = "https://api.pushover.net/1/messages.json"
    pushover_app_token: str | None = None
    pushover_default_user_key: str | None = None
    notification_quiet_hours_start: int = 22
    notification_quiet_hours_end: int = 7
    notification_dedupe_window_seconds: int = 900
