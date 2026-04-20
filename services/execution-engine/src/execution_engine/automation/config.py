from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AutomationSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    enabled_by_default: bool = Field(default=False, alias="AUTOMATION_ENABLED_BY_DEFAULT")
    dry_run_default: bool = Field(default=True, alias="AUTOMATION_DRY_RUN_DEFAULT")
    minimum_confidence: float = Field(default=0.9, alias="AUTOMATION_MIN_CONFIDENCE")
    overnight_minimum_confidence: float = Field(default=0.96, alias="AUTOMATION_OVERNIGHT_MIN_CONFIDENCE")
    max_size_bucket: str = Field(default="small", alias="AUTOMATION_MAX_SIZE_BUCKET")
    max_open_automated_positions: int = Field(default=2, alias="AUTOMATION_MAX_OPEN_POSITIONS")
    stale_health_minutes: int = Field(default=10, alias="AUTOMATION_STALE_HEALTH_MINUTES")
    anomaly_failure_threshold: int = Field(default=3, alias="AUTOMATION_FAILURE_THRESHOLD")
    anomaly_window_minutes: int = Field(default=20, alias="AUTOMATION_ANOMALY_WINDOW_MINUTES")
    max_orders_per_window: int = Field(default=4, alias="AUTOMATION_MAX_ORDERS_PER_WINDOW")
    orders_window_minutes: int = Field(default=15, alias="AUTOMATION_ORDERS_WINDOW_MINUTES")
    poll_interval_seconds: int = Field(default=60, alias="AUTOMATION_POLL_INTERVAL_SECONDS")
