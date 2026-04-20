from __future__ import annotations

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

from kalshi_client import KalshiClientConfig


class MarketStreamSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    service_name: str = "market-stream"
    database_url: str = Field(default="postgresql+asyncpg://kalshi:kalshi@postgres:5432/kalshi", alias="POSTGRES_URL")
    redis_url: str = Field(default="redis://redis:6379/0", alias="REDIS_URL")
    kalshi_stream_watchlist: str = Field(default="", alias="KALSHI_STREAM_WATCHLIST")
    kalshi_env: str = Field(default="demo", alias="KALSHI_ENV")
    kalshi_api_key_id: str | None = Field(default=None, alias="KALSHI_API_KEY_ID")
    kalshi_private_key_pem: str | None = Field(default=None, alias="KALSHI_PRIVATE_KEY_PEM")
    kalshi_private_key_path: str | None = Field(default=None, alias="KALSHI_PRIVATE_KEY_PATH")
    kalshi_api_base_url: str | None = Field(default=None, alias="KALSHI_API_BASE_URL")
    kalshi_ws_url: str | None = Field(default=None, alias="KALSHI_WS_URL")
    cache_latest_state: bool = True
    bootstrap_rest_on_startup: bool = True
    heartbeat_interval_seconds: int = 15
    stale_after_seconds: float = 45.0

    @computed_field
    @property
    def watchlist_tickers(self) -> list[str]:
        return [ticker.strip() for ticker in self.kalshi_stream_watchlist.split(",") if ticker.strip()]

    def build_kalshi_config(self) -> KalshiClientConfig:
        return KalshiClientConfig(
            environment=self.kalshi_env,
            api_key_id=self.kalshi_api_key_id,
            private_key_pem=self.kalshi_private_key_pem,
            private_key_path=self.kalshi_private_key_path,
            api_base_url=self.kalshi_api_base_url,
            ws_url=self.kalshi_ws_url,
            stale_after_seconds=self.stale_after_seconds,
        )
