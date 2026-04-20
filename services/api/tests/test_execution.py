import asyncio
import os
from pathlib import Path

TEST_DB = Path("./data/test_kalshi_execution.db")
if TEST_DB.exists():
    TEST_DB.unlink()

os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{TEST_DB}"
os.environ["DATABASE_URL_SYNC"] = f"sqlite:///{TEST_DB}"
os.environ["DEV_AUTH_TOKEN"] = "local-dev-token"
os.environ["KALSHI_ENABLE_TRADING"] = "false"

from fastapi.testclient import TestClient

from app.main import app
from app.db.base import Base
from app.db.session import engine


async def _prepare_db() -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)


def test_execution_preview_approval_and_kill_switch() -> None:
    asyncio.run(_prepare_db())
    with TestClient(app) as client:
        preview = client.post(
            "/api/execution/preview",
            headers={"Authorization": "Bearer local-dev-token"},
            json={
                "action": "buy",
                "count": 10,
                "side": "yes",
                "ticker": "FED-2026-CUTS",
                "type": "limit",
                "yes_price": 55,
            },
        )
        assert preview.status_code == 200
        order = preview.json()
        assert order["approval_status"] == "pending_approval"
        assert order["requires_manual_approval"] is True

        approved = client.post(
            f"/api/execution/{order['id']}/approve",
            headers={"Authorization": "Bearer local-dev-token"},
        )
        assert approved.status_code == 200
        assert approved.json()["approval_status"] == "approved"

        kill_switch = client.put(
            "/api/execution/kill-switch",
            headers={"Authorization": "Bearer local-dev-token"},
            json={"enabled": False, "reason": "Test freeze"},
        )
        assert kill_switch.status_code == 200
        assert kill_switch.json()["is_enabled"] is False

        audit = client.get(
            "/api/execution/audit",
            headers={"Authorization": "Bearer local-dev-token"},
        )
        assert audit.status_code == 200
        events = [item["event_type"] for item in audit.json()["items"]]
        assert "order_previewed" in events
        assert "order_approved" in events
        assert "kill_switch_updated" in events
