from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(slots=True)
class SmokeConfig:
    environment: str
    web_url: str
    api_url: str
    auth_token: str | None
    expected_mode: str | None
    allow_live: bool
    require_manifest: bool
    require_kalshi: bool

    @classmethod
    def from_env(cls) -> "SmokeConfig":
        environment = os.getenv("SMOKE_ENV", "local")
        return cls(
            environment=environment,
            web_url=os.getenv("SMOKE_WEB_URL", "http://localhost:3000"),
            api_url=os.getenv("SMOKE_API_URL", "http://localhost:8000"),
            auth_token=os.getenv("SMOKE_AUTH_TOKEN", os.getenv("DEV_AUTH_TOKEN")),
            expected_mode=os.getenv("SMOKE_EXPECTED_MODE"),
            allow_live=os.getenv("SMOKE_ALLOW_LIVE", "false").lower() == "true",
            require_manifest=os.getenv("SMOKE_REQUIRE_MANIFEST", "true").lower() == "true",
            require_kalshi=os.getenv("SMOKE_REQUIRE_KALSHI", "false" if environment == "local" else "true").lower() == "true",
        )
