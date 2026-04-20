import asyncio
import os
from datetime import datetime
from pathlib import Path

TEST_DB = Path("./data/test_kalshi_notifications.db")
if TEST_DB.exists():
    TEST_DB.unlink()

current_hour = datetime.now().astimezone().hour
next_hour = (current_hour + 1) % 24

os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{TEST_DB}"
os.environ["DATABASE_URL_SYNC"] = f"sqlite:///{TEST_DB}"
os.environ["DEV_AUTH_TOKEN"] = "local-dev-token"
os.environ["NOTIFICATION_QUIET_HOURS_START"] = str(current_hour)
os.environ["NOTIFICATION_QUIET_HOURS_END"] = str(next_hour)

from fastapi.testclient import TestClient

from app.main import app
from app.db.base import Base
from app.db.session import engine


async def _prepare_db() -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)


def test_notification_quiet_hours_and_dedupe() -> None:
    asyncio.run(_prepare_db())
    with TestClient(app) as client:
        quiet_endpoint = client.post(
            "/api/notifications",
            headers={"Authorization": "Bearer local-dev-token"},
            json={
                "channel": "alerts",
                "destination": "user-key-1",
                "provider": "pwa_push",
                "quiet_hours_enabled": True,
            },
        )
        assert quiet_endpoint.status_code == 201

        quiet_send = client.post(
            "/api/notifications/send",
            headers={"Authorization": "Bearer local-dev-token"},
            json={
                "title": "Quiet test",
                "message": "This should be suppressed by quiet hours.",
                "dedupe_key": "quiet-check",
            },
        )
        assert quiet_send.status_code == 200
        assert quiet_send.json()["items"][0]["status"] == "suppressed_quiet_hours"

        active_endpoint = client.post(
            "/api/notifications",
            headers={"Authorization": "Bearer local-dev-token"},
            json={
                "channel": "alerts",
                "destination": "user-key-2",
                "provider": "pwa_push",
                "quiet_hours_enabled": False,
            },
        )
        assert active_endpoint.status_code == 201

        first = client.post(
            "/api/notifications/send",
            headers={"Authorization": "Bearer local-dev-token"},
            json={
                "title": "Deduped test",
                "message": "First send should go through.",
                "dedupe_key": "dedupe-check",
            },
        )
        assert first.status_code == 200
        statuses = [item["status"] for item in first.json()["items"]]
        assert "sent" in statuses

        second = client.post(
            "/api/notifications/send",
            headers={"Authorization": "Bearer local-dev-token"},
            json={
                "title": "Deduped test",
                "message": "First send should go through.",
                "dedupe_key": "dedupe-check",
            },
        )
        assert second.status_code == 200
        statuses = [item["status"] for item in second.json()["items"]]
        assert "suppressed_duplicate" in statuses
