from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(slots=True)
class ServiceHealthState:
    service_name: str
    started_at: datetime = field(default_factory=utcnow)
    last_heartbeat: datetime = field(default_factory=utcnow)
    healthy: bool = True
    details: dict[str, object] = field(default_factory=dict)

    def mark_heartbeat(self, **details: object) -> None:
        self.last_heartbeat = utcnow()
        if details:
            self.details.update(details)

    def mark_unhealthy(self, **details: object) -> None:
        self.healthy = False
        if details:
            self.details.update(details)

    def mark_healthy(self, **details: object) -> None:
        self.healthy = True
        self.mark_heartbeat(**details)


async def run_health_server(
    state: ServiceHealthState,
    *,
    host: str = "0.0.0.0",
    port: int | None = None,
    stale_after_seconds: int = 180,
) -> asyncio.AbstractServer | None:
    if not port:
        return None

    async def handler(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        try:
            request_line = await reader.readline()
            if not request_line:
                writer.close()
                await writer.wait_closed()
                return

            path = "/"
            parts = request_line.decode("utf-8", errors="ignore").split(" ")
            if len(parts) >= 2:
                path = parts[1]

            while True:
                line = await reader.readline()
                if line in {b"\r\n", b"\n", b""}:
                    break

            is_stale = (utcnow() - state.last_heartbeat).total_seconds() > stale_after_seconds
            status_code = 200
            status = "healthy"
            if path == "/ready" and (not state.healthy or is_stale):
                status_code = 503
                status = "unhealthy" if not state.healthy else "stale"

            payload = {
                "service": state.service_name,
                "status": status,
                "started_at": state.started_at.isoformat(),
                "last_heartbeat": state.last_heartbeat.isoformat(),
                "details": state.details,
            }
            body = json.dumps(payload).encode("utf-8")
            writer.write(
                (
                    f"HTTP/1.1 {status_code} {'OK' if status_code == 200 else 'Service Unavailable'}\r\n"
                    "Content-Type: application/json\r\n"
                    f"Content-Length: {len(body)}\r\n"
                    "Connection: close\r\n\r\n"
                ).encode("utf-8")
            )
            writer.write(body)
            await writer.drain()
        finally:
            writer.close()
            await writer.wait_closed()

    return await asyncio.start_server(handler, host=host, port=port)
