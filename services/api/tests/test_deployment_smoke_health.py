import asyncio
import os
from pathlib import Path

TEST_DB = Path("./data/test_kalshi_smoke_health.db")
if TEST_DB.exists():
    TEST_DB.unlink()

os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{TEST_DB}"
os.environ["DATABASE_URL_SYNC"] = f"sqlite:///{TEST_DB}"
os.environ["DEV_AUTH_TOKEN"] = "local-dev-token"
os.environ["SMOKE_TEST_ENABLE_KALSHI"] = "false"

from fastapi.testclient import TestClient

import app.services.health as health_service
from app.db.base import Base
from app.db.session import engine
from app.main import app


async def _prepare_db() -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)
        await connection.exec_driver_sql("CREATE TABLE IF NOT EXISTS alembic_version (version_num VARCHAR(32) NOT NULL)")
        await connection.exec_driver_sql("DELETE FROM alembic_version")
        await connection.exec_driver_sql("INSERT INTO alembic_version (version_num) VALUES ('20260420_0008')")


def test_smoke_health_route_reports_mode_and_dependencies() -> None:
    asyncio.run(_prepare_db())
    class FakeRedis:
        async def ping(self) -> bool:
            return True

        async def aclose(self) -> None:
            return None

    health_service.Redis.from_url = lambda *_args, **_kwargs: FakeRedis()  # type: ignore[method-assign]
    with TestClient(app) as client:
        response = client.get("/api/health/smoke", headers={"Authorization": "Bearer local-dev-token"})
        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "pass"
        components = {item["component"] for item in payload["checks"]}
        assert "database" in components
        assert "redis" in components
        assert "mode_safety" in components
