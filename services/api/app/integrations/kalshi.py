from __future__ import annotations

from collections.abc import AsyncIterator

from kalshi_client import KalshiRestClient

from app.core.config import get_settings


async def get_kalshi_client() -> AsyncIterator[KalshiRestClient]:
    settings = get_settings()
    async with KalshiRestClient(settings.build_kalshi_config()) as client:
        yield client
