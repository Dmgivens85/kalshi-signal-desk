import os

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./data/test_kalshi_platform.db"
os.environ["DATABASE_URL_SYNC"] = "sqlite:///./data/test_kalshi_platform.db"
os.environ["AUTH_OPTIONAL"] = "true"
os.environ["HEALTHCHECK_ENABLE_EXTERNALS"] = "false"

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_healthcheck() -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_readiness() -> None:
    response = client.get("/api/health/ready")

    assert response.status_code == 200
    body = response.json()
    assert body["service"] == "kalshi-market-intelligence"
    assert "checks" in body
