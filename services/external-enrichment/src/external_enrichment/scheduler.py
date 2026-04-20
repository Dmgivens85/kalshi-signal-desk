from __future__ import annotations

import asyncio
import logging

from .config import ExternalEnrichmentSettings
from .service import ExternalEnrichmentWorker

logger = logging.getLogger(__name__)


class EnrichmentScheduler:
    def __init__(self, settings: ExternalEnrichmentSettings) -> None:
        self.settings = settings
        self.worker = ExternalEnrichmentWorker(settings)

    async def run_forever(self) -> None:
        while True:
            try:
                await self.worker.run_once()
            except Exception as exc:
                logger.exception("external_enrichment_scheduler_failed", extra={"error": str(exc)})
            await asyncio.sleep(self.settings.scheduler_interval_seconds)

    async def run_once(self) -> dict[str, object]:
        return await self.worker.run_once()
