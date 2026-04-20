from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, computed_field

from kalshi_client import KalshiClientConfig, KalshiEnvironment
from kalshi_common import PlatformSettings


class APISettings(PlatformSettings):
    app_version: str = "0.1.0"
    api_docs_enabled: bool = True
    auth_optional: bool = False
    dev_auth_token: str | None = "local-dev-token"
    app_jwt_secret: str | None = "change-me"
    healthcheck_enable_externals: bool = False
    kalshi_api_base_url: str | None = None
    kalshi_ws_url: str | None = None
    kalshi_stream_watchlist: str = Field(default="", alias="KALSHI_STREAM_WATCHLIST")
    execution_mode: str = Field(default="paper", alias="EXECUTION_MODE")
    execution_live_confirmation: bool = Field(default=False, alias="EXECUTION_LIVE_CONFIRMATION")
    paper_fill_mode: str = Field(default="midpoint", alias="PAPER_FILL_MODE")
    paper_slippage_bps: int = Field(default=25, alias="PAPER_SLIPPAGE_BPS")
    paper_partial_fill_ratio: float = Field(default=0.5, alias="PAPER_PARTIAL_FILL_RATIO")
    paper_default_cash_cents: int = Field(default=1_000_000, alias="PAPER_DEFAULT_CASH_CENTS")
    notification_deep_link_base: str = Field(default="http://localhost:3000", alias="NOTIFICATION_DEEP_LINK_BASE")
    notification_delivery_retry_attempts: int = Field(default=3, alias="NOTIFICATION_DELIVERY_RETRY_ATTEMPTS")
    notifier_scheduler_interval_seconds: int = Field(default=60, alias="NOTIFIER_SCHEDULER_INTERVAL_SECONDS")
    market_stream_health_url: str | None = Field(default="http://market-stream:9090/ready", alias="MARKET_STREAM_HEALTH_URL")
    external_enrichment_health_url: str | None = Field(default="http://external-enrichment:9090/ready", alias="EXTERNAL_ENRICHMENT_HEALTH_URL")
    signal_engine_health_url: str | None = Field(default="http://signal-engine:9090/ready", alias="SIGNAL_ENGINE_HEALTH_URL")
    execution_engine_health_url: str | None = Field(default="http://execution-engine:9090/ready", alias="EXECUTION_ENGINE_HEALTH_URL")
    notifier_health_url: str | None = Field(default="http://notifier:9090/ready", alias="NOTIFIER_HEALTH_URL")
    scheduler_health_url: str | None = Field(default="http://scheduler:9090/ready", alias="SCHEDULER_HEALTH_URL")
    smoke_test_enable_kalshi: bool = Field(default=True, alias="SMOKE_TEST_ENABLE_KALSHI")

    @computed_field
    @property
    def auth_mode(self) -> str:
        if self.dev_auth_token:
            return "dev-token+jwt"
        return "jwt"

    @computed_field
    @property
    def resolved_execution_mode(self) -> str:
        requested = self.execution_mode.lower()
        if requested == "live" and not self.execution_live_confirmation:
            return "disabled"
        if requested not in {"disabled", "paper", "live"}:
            return "paper"
        return requested

    @computed_field
    @property
    def live_trading_enabled(self) -> bool:
        return self.resolved_execution_mode == "live"

    @computed_field
    @property
    def watchlist_tickers(self) -> list[str]:
        return [ticker.strip() for ticker in self.kalshi_stream_watchlist.split(",") if ticker.strip()]

    def build_kalshi_config(self) -> KalshiClientConfig:
        env = (
            KalshiEnvironment.PRODUCTION
            if self.kalshi_env.lower() in {"prod", "production"}
            else KalshiEnvironment.DEMO
        )
        return KalshiClientConfig(
            environment=env,
            api_key_id=self.kalshi_api_key_id,
            private_key_pem=self.kalshi_private_key_pem,
            private_key_path=Path(self.kalshi_private_key_path) if self.kalshi_private_key_path else None,
            api_base_url=self.kalshi_api_base_url or self.kalshi_api_url,
            ws_url=self.kalshi_ws_url,
            timeout_seconds=self.kalshi_request_timeout_seconds,
            enable_trading=self.kalshi_enable_trading and self.live_trading_enabled,
        )


@lru_cache
def get_settings() -> APISettings:
    return APISettings()
