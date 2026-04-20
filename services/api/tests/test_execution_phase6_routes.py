import asyncio
import os
from pathlib import Path

TEST_DB = Path("./data/test_kalshi_execution_phase6.db")
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


def test_phase6_orders_positions_risk_routes() -> None:
    asyncio.run(_prepare_db())
    with TestClient(app) as client:
        preview = client.post(
            "/api/orders/preview",
            headers={"Authorization": "Bearer local-dev-token"},
            json={
                "signal_summary": "External confirmation is stronger than current Kalshi pricing.",
                "overnight_flag": False,
                "confidence_score": 0.84,
                "order": {
                    "action": "buy",
                    "count": 6,
                    "side": "yes",
                    "ticker": "FED-2026-CUTS",
                    "type": "limit",
                    "yes_price": 57,
                    "time_in_force": "day",
                    "post_only": True,
                    "reduce_only": False,
                },
            },
        )
        assert preview.status_code == 200
        order = preview.json()
        assert order["approval_status"] in {"pending_approval", "blocked"}

        approvals = client.get("/api/approvals/pending", headers={"Authorization": "Bearer local-dev-token"})
        assert approvals.status_code == 200
        assert any(item["id"] == order["id"] for item in approvals.json()["items"])

        approved = client.post(
            f"/api/orders/{order['id']}/approve",
            headers={"Authorization": "Bearer local-dev-token"},
            json={"notes": "Looks good from mobile review."},
        )
        assert approved.status_code == 200
        assert approved.json()["approval_status"] == "approved"

        positions = client.get("/api/positions", headers={"Authorization": "Bearer local-dev-token"})
        assert positions.status_code == 200
        assert "items" in positions.json()

        risk = client.get("/api/risk", headers={"Authorization": "Bearer local-dev-token"})
        assert risk.status_code == 200
        assert "limits" in risk.json()
        assert "status" in risk.json()

        kill = client.post(
            "/api/risk/kill-switch",
            headers={"Authorization": "Bearer local-dev-token"},
            json={"enabled": False, "reason": "Phase 6 test"},
        )
        assert kill.status_code == 200
        assert kill.json()["is_enabled"] is False
