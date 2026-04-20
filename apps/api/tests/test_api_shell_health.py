from fastapi.testclient import TestClient

from api_shell.main import app


def test_api_shell_health() -> None:
    client = TestClient(app)
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
