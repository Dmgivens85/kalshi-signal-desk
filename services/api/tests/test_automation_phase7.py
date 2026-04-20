import asyncio
import os
from pathlib import Path

TEST_DB = Path("./data/test_kalshi_automation_phase7.db")
if TEST_DB.exists():
    TEST_DB.unlink()

os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{TEST_DB}"
os.environ["DATABASE_URL_SYNC"] = f"sqlite:///{TEST_DB}"
os.environ["DEV_AUTH_TOKEN"] = "local-dev-token"
os.environ["KALSHI_ENABLE_TRADING"] = "false"

from fastapi.testclient import TestClient

from app.main import app
from app.db.base import Base
from app.db.models import ServiceHealthEvent, SignalRecord
from app.db.session import SessionLocal, engine


async def _prepare_db() -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)


async def _seed_signal() -> None:
    async with SessionLocal() as session:
        session.add(ServiceHealthEvent(service_name="market-stream", status="healthy", detail="ok"))
        signal = SignalRecord(
            market_ticker="FED-2026-CUTS",
            signal_type="fused_external_consensus",
            thesis="External consensus is materially above current Kalshi pricing.",
            confidence=0.95,
            confidence_score=0.95,
            horizon="overnight",
            status="active",
            recommended_action="buy_yes",
            reason_summary="Confidence and external confirmation both clear the automation bar.",
            suggested_position_size_bucket="small",
            alert_classification="critical_opportunity",
        )
        session.add(signal)
        await session.commit()


def test_phase7_selective_automation_dry_run_routes() -> None:
    asyncio.run(_prepare_db())
    asyncio.run(_seed_signal())
    with TestClient(app) as client:
        status = client.get("/api/automation/status", headers={"Authorization": "Bearer local-dev-token"})
        assert status.status_code == 200
        assert status.json()["global_enabled"] is False

        enabled = client.post("/api/automation/enable", headers={"Authorization": "Bearer local-dev-token"})
        assert enabled.status_code == 200
        assert enabled.json()["is_enabled"] is True

        policy = client.put(
            "/api/automation/policies",
            headers={"Authorization": "Bearer local-dev-token"},
            json={
                "name": "macro-dry-run",
                "enabled": True,
                "dry_run": True,
                "user_opt_in_enabled": True,
                "allowed_market_tickers": ["FED-2026-CUTS"],
                "allowed_categories": [],
                "min_confidence_score": 0.9,
                "overnight_min_confidence_score": 0.94,
                "max_size_bucket": "small",
                "max_open_automated_positions": 1,
                "notes": "Dry run only."
            },
        )
        assert policy.status_code == 200
        assert policy.json()["is_enabled"] is True

        evaluate = client.post("/api/automation/evaluate", headers={"Authorization": "Bearer local-dev-token"})
        assert evaluate.status_code == 200
        assert evaluate.json()["processed"] >= 1

        events = client.get("/api/automation/events", headers={"Authorization": "Bearer local-dev-token"})
        assert events.status_code == 200
        event_types = [item["event_type"] for item in events.json()["items"]]
        assert "eligibility_decided" in event_types
        assert "dry_run" in event_types

        failures = client.get("/api/automation/failures", headers={"Authorization": "Bearer local-dev-token"})
        assert failures.status_code == 200
        assert "items" in failures.json()

        orders = client.get("/api/orders", headers={"Authorization": "Bearer local-dev-token"})
        assert orders.status_code == 200
        assert len(orders.json()["items"]) >= 1
