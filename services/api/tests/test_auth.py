import os

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./data/test_kalshi_platform.db"
os.environ["DATABASE_URL_SYNC"] = "sqlite:///./data/test_kalshi_platform.db"
os.environ["DEV_AUTH_TOKEN"] = "local-dev-token"

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_session_uses_dev_token() -> None:
    response = client.get("/api/auth/session", headers={"Authorization": "Bearer local-dev-token"})

    assert response.status_code == 200
    assert response.json()["subject"] == "dev-user"
