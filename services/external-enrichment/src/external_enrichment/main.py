from __future__ import annotations

import asyncio
import logging
import os

from kalshi_signal_shared import ServiceHealthState, run_health_server
from .config import ExternalEnrichmentSettings
from .scheduler import EnrichmentScheduler

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


async def _run() -> None:
    settings = ExternalEnrichmentSettings()
    scheduler = EnrichmentScheduler(settings)
    state = ServiceHealthState(settings.service_name)
    health_server = await run_health_server(
        state,
        port=int(os.getenv("SERVICE_HEALTH_PORT", "0") or "0"),
        stale_after_seconds=int(os.getenv("SERVICE_HEALTH_STALE_AFTER_SECONDS", "300")),
    )
    heartbeat_task = asyncio.create_task(_heartbeat_loop(state, settings.scheduler_interval_seconds))
    try:
        await scheduler.run_forever()
    finally:
        heartbeat_task.cancel()
        if health_server is not None:
            health_server.close()
            await health_server.wait_closed()


async def _heartbeat_loop(state: ServiceHealthState, interval_seconds: int) -> None:
    while True:
        state.mark_healthy()
        await asyncio.sleep(max(interval_seconds, 15))


def main() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    main()
