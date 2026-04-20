from __future__ import annotations

import asyncio
import logging
import os

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from kalshi_signal_shared import ServiceHealthState, run_health_server
from .config import NotifierSettings
from .delivery import NotificationDeliveryWorkflow

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


async def run_loop(settings: NotifierSettings) -> None:
    engine = create_async_engine(settings.database_url, future=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    state = ServiceHealthState(settings.service_name)
    health_server = await run_health_server(
        state,
        port=int(os.getenv("SERVICE_HEALTH_PORT", "0") or "0"),
        stale_after_seconds=int(os.getenv("SERVICE_HEALTH_STALE_AFTER_SECONDS", "300")),
    )
    try:
        while True:
            async with session_factory() as session:
                state.mark_healthy(provider=settings.provider)
                workflow = NotificationDeliveryWorkflow(settings, session)
                try:
                    await workflow.process_signal_queue()
                    await session.commit()
                finally:
                    await workflow.aclose()
            await asyncio.sleep(settings.scheduler_interval_seconds)
    finally:
        if health_server is not None:
            health_server.close()
            await health_server.wait_closed()
        await engine.dispose()


def main() -> None:
    asyncio.run(run_loop(NotifierSettings()))


if __name__ == "__main__":
    main()
