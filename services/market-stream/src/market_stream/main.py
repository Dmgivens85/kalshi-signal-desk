from __future__ import annotations

import asyncio
import logging
import os

from kalshi_signal_shared import ServiceHealthState, run_health_server
from .config import MarketStreamSettings
from .service import MarketStreamService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)


async def _run() -> None:
    settings = MarketStreamSettings()
    service = MarketStreamService(settings)
    state = ServiceHealthState(settings.service_name)
    health_server = await run_health_server(
        state,
        port=int(os.getenv("SERVICE_HEALTH_PORT", "0") or "0"),
        stale_after_seconds=int(os.getenv("SERVICE_HEALTH_STALE_AFTER_SECONDS", "180")),
    )
    heartbeat_task = asyncio.create_task(_heartbeat_loop(state, settings.heartbeat_interval_seconds))
    try:
        await service.start()
    finally:
        heartbeat_task.cancel()
        if health_server is not None:
            health_server.close()
            await health_server.wait_closed()
        await service.stop()


async def _heartbeat_loop(state: ServiceHealthState, interval_seconds: int) -> None:
    while True:
        state.mark_healthy()
        await asyncio.sleep(interval_seconds)


def main() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    main()
