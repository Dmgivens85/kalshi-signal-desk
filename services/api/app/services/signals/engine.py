from __future__ import annotations

from signal_engine.config import SignalEngineSettings
from signal_engine.service import SignalEngineService

from app.core.config import APISettings
from sqlalchemy.ext.asyncio import AsyncSession


class SignalEngine:
    def __init__(self, settings: APISettings, db: AsyncSession) -> None:
        self.settings = settings
        self.db = db
        self.service = SignalEngineService(
            SignalEngineSettings(database_url=settings.database_url, redis_url=settings.redis_url),
            db,
        )

    async def run(self) -> dict[str, object]:
        return await self.service.run()
