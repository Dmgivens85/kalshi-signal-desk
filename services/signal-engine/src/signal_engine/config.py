from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class SignalEngineSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    service_name: str = "signal-engine"
    database_url: str = Field(default="postgresql+asyncpg://kalshi:kalshi@postgres:5432/kalshi", alias="POSTGRES_URL")
    redis_url: str = Field(default="redis://redis:6379/0", alias="REDIS_URL")
    loop_interval_seconds: int = 180
    daytime_confidence_threshold: float = 0.62
    overnight_confidence_threshold: float = 0.82
    overnight_risk_penalty_max: float = 0.22
    overnight_min_liquidity_score: float = 0.4
    overnight_max_spread_width: float = 0.16
    duplicate_suppression_minutes: int = 45
    cooldown_minutes: int = 90
    overnight_start_hour: int = 22
    overnight_end_hour: int = 7
    critical_priority_threshold: float = 0.86
    risk_warning_threshold: float = 0.72
