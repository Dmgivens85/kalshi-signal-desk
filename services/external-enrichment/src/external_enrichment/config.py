from __future__ import annotations

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ExternalEnrichmentSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    service_name: str = "external-enrichment"
    database_url: str = Field(default="postgresql+asyncpg://kalshi:kalshi@postgres:5432/kalshi", alias="POSTGRES_URL")
    redis_url: str = Field(default="redis://redis:6379/0", alias="REDIS_URL")
    scheduler_interval_seconds: int = 300
    sportsbook_primary_url: str | None = Field(default=None, alias="SPORTSBOOK_ODDS_API_URL")
    sportsbook_secondary_url: str | None = Field(default=None, alias="SPORTSBOOK_SECONDARY_API_URL")
    polymarket_api_url: str | None = Field(default=None, alias="POLYMARKET_API_URL")
    metaculus_api_url: str | None = Field(default=None, alias="METACULUS_API_URL")
    manifold_api_url: str | None = Field(default=None, alias="MANIFOLD_API_URL")
    news_api_url: str | None = Field(default=None, alias="NEWS_API_URL")
    news_api_key: str | None = Field(default=None, alias="NEWS_API_KEY")
    watchlist_tickers: str = Field(default="", alias="KALSHI_STREAM_WATCHLIST")
    request_timeout_seconds: float = 10.0

    @computed_field
    @property
    def configured_watchlist(self) -> list[str]:
        return [ticker.strip() for ticker in self.watchlist_tickers.split(",") if ticker.strip()]
