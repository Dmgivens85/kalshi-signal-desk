from __future__ import annotations

import asyncio
import logging
import os

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import APISettings
from app.services.execution import GuardedExecutionService
from kalshi_signal_shared import ServiceHealthState, run_health_server
from kalshi_client import KalshiHttpClient
from .automation import AutomationRunner, AutomationSettings
from .config import ExecutionEngineSettings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)


async def run_loop(settings: ExecutionEngineSettings) -> None:
    api_settings = APISettings()
    engine = create_async_engine(settings.database_url, future=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    kalshi = KalshiHttpClient(api_settings.build_kalshi_config())
    state = ServiceHealthState(settings.service_name)
    health_server = await run_health_server(
        state,
        port=int(os.getenv("SERVICE_HEALTH_PORT", "0") or "0"),
        stale_after_seconds=int(os.getenv("SERVICE_HEALTH_STALE_AFTER_SECONDS", "300")),
    )
    try:
        while True:
            async with session_factory() as session:
                logger.info("execution_engine_heartbeat")
                state.mark_healthy(mode=api_settings.resolved_execution_mode)
                execution = GuardedExecutionService(api_settings, session, kalshi)
                runner = AutomationRunner(AutomationSettings(), session, execution)
                await runner.evaluate_pending_signals()
                await session.commit()
            await asyncio.sleep(AutomationSettings().poll_interval_seconds)
    finally:
        if health_server is not None:
            health_server.close()
            await health_server.wait_closed()
        await kalshi.aclose()
        await engine.dispose()


def main() -> None:
    asyncio.run(run_loop(ExecutionEngineSettings()))


if __name__ == "__main__":
    main()
