import os

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./data/test_kalshi_platform.db"
os.environ["DATABASE_URL_SYNC"] = "sqlite:///./data/test_kalshi_platform.db"
os.environ["AUTH_OPTIONAL"] = "true"
os.environ["KALSHI_STREAM_WATCHLIST"] = "TEST-YES-001,TEST-YES-002"

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app
from kalshi_client import KalshiRequestSigner, normalize_signing_path


get_settings.cache_clear()
client = TestClient(app)


def _private_key_pem() -> str:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")


def test_signing_path_strips_query_string() -> None:
    assert normalize_signing_path("/markets?limit=10") == "/markets"
    assert normalize_signing_path("https://demo-api.kalshi.co/trade-api/v2/markets?limit=10") == "/trade-api/v2/markets"


def test_signer_builds_kalshi_headers() -> None:
    signer = KalshiRequestSigner(api_key_id="test-key", private_key_pem=_private_key_pem())
    headers = signer.build_auth_headers("GET", "/markets?limit=10", timestamp_ms="1234567890")
    assert headers["KALSHI-ACCESS-KEY"] == "test-key"
    assert headers["KALSHI-ACCESS-TIMESTAMP"] == "1234567890"
    assert "KALSHI-ACCESS-SIGNATURE" in headers


def test_watchlist_route_reads_configured_tickers() -> None:
    response = client.get("/api/watchlist")
    assert response.status_code == 200
    body = response.json()
    assert body["watchlist"] == ["TEST-YES-001", "TEST-YES-002"]
