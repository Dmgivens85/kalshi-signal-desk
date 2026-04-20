import os
import asyncio
from pathlib import Path

TEST_DB = Path("./data/test_kalshi_signal_phase4_routes.db")
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


def test_market_signal_summary_route() -> None:
    asyncio.run(_prepare_db())
    with TestClient(app) as client:
        run_response = client.post("/api/signals/run", headers={"Authorization": "Bearer local-dev-token"})
        assert run_response.status_code == 200
        ticker = run_response.json()["items"][0]["market_ticker"]
        summary_response = client.get(f"/api/markets/{ticker}/signal-summary")

    assert summary_response.status_code == 200
    body = summary_response.json()
    assert body["market_ticker"] == ticker
    assert body["signal"] is not None
