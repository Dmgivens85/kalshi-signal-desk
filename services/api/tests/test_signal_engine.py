import os
import asyncio
from pathlib import Path

TEST_DB = Path("./data/test_kalshi_signal_engine.db")
if TEST_DB.exists():
    TEST_DB.unlink()

os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{TEST_DB}"
os.environ["DATABASE_URL_SYNC"] = f"sqlite:///{TEST_DB}"
os.environ["DEV_AUTH_TOKEN"] = "local-dev-token"
os.environ["HEALTHCHECK_ENABLE_EXTERNALS"] = "false"

from fastapi.testclient import TestClient

from app.main import app
from app.db.base import Base
from app.db.session import engine


async def _prepare_db() -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)


def test_signal_engine_run_creates_alerts() -> None:
    asyncio.run(_prepare_db())
    with TestClient(app) as client:
        response = client.post("/api/signals/run", headers={"Authorization": "Bearer local-dev-token"})

    assert response.status_code == 200
    body = response.json()
    assert body["signals_created"] >= 1
    assert body["items"][0]["suggested_action"] in {"consider_yes", "consider_no", "watch"}
    assert "confidence_score" in body["items"][0]
    assert "overnight_priority_score" in body["items"][0]
    assert "notification_candidate" in body["items"][0]


def test_signal_routes_expose_ranked_views() -> None:
    asyncio.run(_prepare_db())
    with TestClient(app) as client:
        run_response = client.post("/api/signals/run", headers={"Authorization": "Bearer local-dev-token"})
        assert run_response.status_code == 200

        top_response = client.get("/api/signals/top")
        overnight_response = client.get("/api/signals/overnight")

    assert top_response.status_code == 200
    assert "items" in top_response.json()
    assert overnight_response.status_code == 200
    assert "items" in overnight_response.json()
