from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class NotifierSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    service_name: str = "notifier"
    database_url: str = Field(default="postgresql+asyncpg://kalshi:kalshi@postgres:5432/kalshi", alias="POSTGRES_URL")
    redis_url: str = Field(default="redis://redis:6379/0", alias="REDIS_URL")
    pushover_api_url: str = Field(default="https://api.pushover.net/1/messages.json", alias="PUSHOVER_API_URL")
    pushover_app_token: str | None = Field(default=None, alias="PUSHOVER_APP_TOKEN")
    pushover_default_user_key: str | None = Field(default=None, alias="PUSHOVER_DEFAULT_USER_KEY")
    default_deep_link_base: str = Field(default="http://localhost:3000", alias="NOTIFICATION_DEEP_LINK_BASE")
    execution_mode: str = Field(default="paper", alias="EXECUTION_MODE")
    dedupe_ttl_seconds: int = Field(default=1800, alias="NOTIFICATION_DEDUPE_WINDOW_SECONDS")
    delivery_retry_attempts: int = Field(default=3, alias="NOTIFICATION_DELIVERY_RETRY_ATTEMPTS")
    quiet_hours_start: int = Field(default=22, alias="NOTIFICATION_QUIET_HOURS_START")
    quiet_hours_end: int = Field(default=7, alias="NOTIFICATION_QUIET_HOURS_END")
    scheduler_interval_seconds: int = Field(default=60, alias="NOTIFIER_SCHEDULER_INTERVAL_SECONDS")
