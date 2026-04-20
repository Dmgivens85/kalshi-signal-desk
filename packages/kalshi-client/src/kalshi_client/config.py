from __future__ import annotations

from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, computed_field


class KalshiEnvironment(StrEnum):
    PRODUCTION = "production"
    DEMO = "demo"


class KalshiClientConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    environment: KalshiEnvironment = KalshiEnvironment.DEMO
    api_key_id: str | None = None
    private_key_pem: str | None = None
    private_key_path: Path | None = None
    base_url: str | None = None
    websocket_url: str | None = None
    request_timeout_seconds: float = Field(default=10.0, gt=0)
    max_retries: int = Field(default=3, ge=0)

    @computed_field
    @property
    def resolved_base_url(self) -> str:
        if self.base_url:
            return self.base_url.rstrip("/")

        if self.environment == KalshiEnvironment.PRODUCTION:
            return "https://api.elections.kalshi.com/trade-api/v2"

        return "https://demo-api.kalshi.co/trade-api/v2"

    @computed_field
    @property
    def resolved_websocket_url(self) -> str:
        if self.websocket_url:
            return self.websocket_url.rstrip("/")

        if self.environment == KalshiEnvironment.PRODUCTION:
            return "wss://api.elections.kalshi.com/trade-api/ws/v2"

        return "wss://demo-api.kalshi.co/trade-api/ws/v2"

    def load_private_key_pem(self) -> str | None:
        if self.private_key_pem:
            return self.private_key_pem

        if self.private_key_path:
            return self.private_key_path.read_text(encoding="utf-8")

        return None
