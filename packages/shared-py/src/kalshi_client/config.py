from __future__ import annotations

from enum import StrEnum
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from .errors import KalshiConfigurationError


class KalshiEnvironment(StrEnum):
    DEMO = "demo"
    PRODUCTION = "prod"


DEFAULT_API_URLS: dict[KalshiEnvironment, str] = {
    KalshiEnvironment.DEMO: "https://demo-api.kalshi.co/trade-api/v2",
    KalshiEnvironment.PRODUCTION: "https://api.elections.kalshi.com/trade-api/v2",
}

DEFAULT_WS_URLS: dict[KalshiEnvironment, str] = {
    KalshiEnvironment.DEMO: "wss://demo-api.kalshi.co/trade-api/ws/v2",
    KalshiEnvironment.PRODUCTION: "wss://api.elections.kalshi.com/trade-api/ws/v2",
}


class KalshiClientConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    environment: KalshiEnvironment = Field(default=KalshiEnvironment.DEMO, alias="KALSHI_ENV")
    api_key_id: str | None = Field(default=None, alias="KALSHI_API_KEY_ID")
    private_key_pem: str | None = Field(default=None, alias="KALSHI_PRIVATE_KEY_PEM")
    private_key_path: Path | None = Field(default=None, alias="KALSHI_PRIVATE_KEY_PATH")
    api_base_url: str | None = Field(default=None, alias="KALSHI_API_BASE_URL")
    ws_url: str | None = Field(default=None, alias="KALSHI_WS_URL")
    timeout_seconds: float = 10.0
    max_retries: int = 3
    connect_timeout_seconds: float = 10.0
    stale_after_seconds: float = 45.0
    enable_trading: bool = False

    @field_validator("environment", mode="before")
    @classmethod
    def normalize_environment(cls, value: object) -> object:
        if isinstance(value, str):
            lowered = value.lower()
            if lowered in {"prod", "production"}:
                return KalshiEnvironment.PRODUCTION
            if lowered in {"demo", "sandbox"}:
                return KalshiEnvironment.DEMO
        return value

    @property
    def resolved_api_base_url(self) -> str:
        return self.api_base_url or DEFAULT_API_URLS[self.environment]

    @property
    def resolved_ws_url(self) -> str:
        return self.ws_url or DEFAULT_WS_URLS[self.environment]

    def require_credentials(self) -> None:
        if not self.api_key_id:
            raise KalshiConfigurationError("KALSHI_API_KEY_ID is required for authenticated Kalshi access.")
        if self.private_key_pem is None and self.private_key_path is None:
            raise KalshiConfigurationError(
                "Either KALSHI_PRIVATE_KEY_PEM or KALSHI_PRIVATE_KEY_PATH is required for authenticated Kalshi access."
            )

    def load_private_key_pem(self) -> str:
        self.require_credentials()
        if self.private_key_pem:
            return self.private_key_pem
        assert self.private_key_path is not None
        if not self.private_key_path.exists():
            raise KalshiConfigurationError(
                f"Kalshi private key path does not exist: {self.private_key_path}"
            )
        return self.private_key_path.read_text(encoding="utf-8")
