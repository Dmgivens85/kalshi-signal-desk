from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ExecutionEngineSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    service_name: str = "execution-engine"
    database_url: str = Field(default="sqlite+aiosqlite:///./data/kalshi_platform.db", alias="POSTGRES_URL")
    overnight_mode_enabled: bool = Field(default=True, alias="OVERNIGHT_MODE_ENABLED")
    max_exposure_per_market_cents: int = Field(default=25_000, alias="RISK_MAX_EXPOSURE_PER_MARKET_CENTS")
    max_exposure_per_category_cents: int = Field(default=75_000, alias="RISK_MAX_EXPOSURE_PER_CATEGORY_CENTS")
    max_daily_drawdown_cents: int = Field(default=50_000, alias="RISK_MAX_DAILY_DRAWDOWN_CENTS")
    max_simultaneous_positions: int = Field(default=8, alias="RISK_MAX_SIMULTANEOUS_POSITIONS")
    max_spread_cents: int = Field(default=12, alias="RISK_MAX_SPREAD_CENTS")
    min_liquidity: int = Field(default=100, alias="RISK_MIN_LIQUIDITY")
    max_category_concentration: float = Field(default=0.55, alias="RISK_MAX_CATEGORY_CONCENTRATION")
    cooldown_after_loss_minutes: int = Field(default=90, alias="RISK_COOLDOWN_AFTER_LOSS_MINUTES")
    min_time_to_resolution_minutes: int = Field(default=60, alias="RISK_MIN_TIME_TO_RESOLUTION_MINUTES")
    overnight_max_spread_cents: int = Field(default=8, alias="RISK_OVERNIGHT_MAX_SPREAD_CENTS")
    overnight_min_liquidity: int = Field(default=250, alias="RISK_OVERNIGHT_MIN_LIQUIDITY")
