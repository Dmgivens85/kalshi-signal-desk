from __future__ import annotations

import asyncio
import os

from kalshi_signal_shared import ServiceHealthState, run_health_server


async def _run() -> None:
    state = ServiceHealthState("scheduler")
    health_server = await run_health_server(
        state,
        port=int(os.getenv("SERVICE_HEALTH_PORT", "0") or "0"),
        stale_after_seconds=int(os.getenv("SERVICE_HEALTH_STALE_AFTER_SECONDS", "300")),
    )
    try:
        while True:
            state.mark_healthy(status="idle")
            await asyncio.sleep(30)
    finally:
        if health_server is not None:
            health_server.close()
            await health_server.wait_closed()


def main() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    main()
