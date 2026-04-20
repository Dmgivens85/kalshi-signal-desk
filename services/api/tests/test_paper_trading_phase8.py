import asyncio
import os
from pathlib import Path

TEST_DB = Path("./data/test_kalshi_paper_phase8.db")
if TEST_DB.exists():
    TEST_DB.unlink()

os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{TEST_DB}"
os.environ["DATABASE_URL_SYNC"] = f"sqlite:///{TEST_DB}"
os.environ["DEV_AUTH_TOKEN"] = "local-dev-token"
os.environ["KALSHI_ENABLE_TRADING"] = "false"
os.environ["EXECUTION_MODE"] = "paper"

from fastapi.testclient import TestClient

from app.main import app
from app.db.base import Base
from app.db.models import MarketSnapshot, SignalRecord
from app.db.session import SessionLocal, engine


async def _prepare_db() -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)


async def _seed_market_and_signal() -> None:
    async with SessionLocal() as session:
        session.add(
            MarketSnapshot(
                market_ticker="FED-2026-CUTS",
                event_ticker="FED-2026",
                title="Will the Fed cut by June 2026?",
                status="open",
                last_price=58,
                yes_bid=57,
                yes_ask=59,
                volume=1000,
                open_interest=200,
                snapshot_type="ticker",
                liquidity=300,
            )
        )
        session.add(
            SignalRecord(
                market_ticker="FED-2026-CUTS",
                signal_type="fused_external_consensus",
                thesis="External consensus remains above current Kalshi price.",
                confidence=0.9,
                confidence_score=0.9,
                horizon="overnight",
                status="active",
                recommended_action="buy_yes",
                reason_summary="High-confidence paper trade candidate.",
                suggested_position_size_bucket="small",
            )
        )
        await session.commit()


def test_phase8_paper_mode_and_replay_routes() -> None:
    asyncio.run(_prepare_db())
    asyncio.run(_seed_market_and_signal())
    with TestClient(app) as client:
        status = client.get("/api/paper/status", headers={"Authorization": "Bearer local-dev-token"})
        assert status.status_code == 200
        assert status.json()["mode"] == "paper"

        preview = client.post(
            "/api/orders/preview",
            headers={"Authorization": "Bearer local-dev-token"},
            json={"signal_id": "1"},  # invalid on purpose to ensure direct path below is used
        )
        assert preview.status_code == 404 or preview.status_code == 422

        create_preview = client.post(
            "/api/orders/preview",
            headers={"Authorization": "Bearer local-dev-token"},
            json={
                "signal_summary": "Paper-mode candidate.",
                "confidence_score": 0.9,
                "order": {
                    "ticker": "FED-2026-CUTS",
                    "action": "buy",
                    "side": "yes",
                    "count": 8,
                    "type": "limit",
                    "yes_price": 58
                },
            },
        )
        assert create_preview.status_code == 200
        order = create_preview.json()

        approved = client.post(
            f"/api/orders/{order['id']}/approve",
            headers={"Authorization": "Bearer local-dev-token"},
            json={"notes": "Approve paper trade."},
        )
        assert approved.status_code == 200

        submitted = client.post(
            f"/api/orders/{order['id']}/submit",
            headers={"Authorization": "Bearer local-dev-token"},
        )
        assert submitted.status_code == 200
        assert submitted.json()["mode"] == "paper"
        assert submitted.json()["simulated"] is True

        paper_orders = client.get("/api/paper/orders", headers={"Authorization": "Bearer local-dev-token"})
        assert paper_orders.status_code == 200
        assert len(paper_orders.json()["items"]) >= 1

        paper_positions = client.get("/api/paper/positions", headers={"Authorization": "Bearer local-dev-token"})
        assert paper_positions.status_code == 200
        assert "items" in paper_positions.json()

        performance = client.get("/api/paper/performance", headers={"Authorization": "Bearer local-dev-token"})
        assert performance.status_code == 200
        assert "realized_pnl_cents" in performance.json()

        replay = client.post(
            "/api/paper/replay/start",
            headers={"Authorization": "Bearer local-dev-token"},
            json={"name": "paper-replay", "market_ticker": "FED-2026-CUTS", "max_events": 50},
        )
        assert replay.status_code == 200
        run_id = replay.json()["run_id"]

        replay_detail = client.get(f"/api/paper/replay/{run_id}", headers={"Authorization": "Bearer local-dev-token"})
        assert replay_detail.status_code == 200

        runs = client.get("/api/paper/simulation-runs", headers={"Authorization": "Bearer local-dev-token"})
        assert runs.status_code == 200
        assert len(runs.json()["items"]) >= 1
