from __future__ import annotations

import base64
import time
from pathlib import Path
from urllib.parse import urlsplit

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from .config import KalshiClientConfig
from .errors import KalshiConfigurationError, KalshiSigningError

WS_SIGNING_PATH = "/trade-api/ws/v2"


def normalize_signing_path(path: str) -> str:
    parsed = urlsplit(path)
    if parsed.scheme or parsed.netloc:
        return parsed.path or "/"
    return path.split("?", 1)[0] or "/"


class KalshiRequestSigner:
    def __init__(self, api_key_id: str, private_key_pem: str) -> None:
        if not api_key_id:
            raise KalshiConfigurationError("Kalshi API key ID is required.")
        if not private_key_pem:
            raise KalshiConfigurationError("Kalshi private key PEM is required.")

        self.api_key_id = api_key_id
        self.private_key = serialization.load_pem_private_key(private_key_pem.encode("utf-8"), password=None)
        if not isinstance(self.private_key, rsa.RSAPrivateKey):
            raise KalshiConfigurationError("Kalshi private key must be RSA.")

    @classmethod
    def from_path(cls, api_key_id: str, private_key_path: str | Path) -> "KalshiRequestSigner":
        return cls(api_key_id=api_key_id, private_key_pem=Path(private_key_path).read_text(encoding="utf-8"))

    @classmethod
    def from_config(cls, config: KalshiClientConfig) -> "KalshiRequestSigner":
        return cls(api_key_id=config.api_key_id or "", private_key_pem=config.load_private_key_pem())

    def sign(self, timestamp_ms: str, method: str, request_path: str) -> str:
        try:
            payload = f"{timestamp_ms}{method.upper()}{normalize_signing_path(request_path)}".encode("utf-8")
            signature = self.private_key.sign(
                payload,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.DIGEST_LENGTH,
                ),
                hashes.SHA256(),
            )
        except Exception as exc:  # pragma: no cover - cryptography failures are environment-specific
            raise KalshiSigningError("Failed to sign Kalshi request.") from exc
        return base64.b64encode(signature).decode("utf-8")

    def build_auth_headers(
        self,
        method: str,
        request_path: str,
        *,
        timestamp_ms: str | None = None,
    ) -> dict[str, str]:
        issued_at = timestamp_ms or str(int(time.time() * 1000))
        return {
            "KALSHI-ACCESS-KEY": self.api_key_id,
            "KALSHI-ACCESS-TIMESTAMP": issued_at,
            "KALSHI-ACCESS-SIGNATURE": self.sign(issued_at, method, request_path),
        }


def build_kalshi_auth_headers(
    config: KalshiClientConfig,
    method: str,
    request_path: str,
    *,
    timestamp_ms: str | None = None,
) -> dict[str, str]:
    signer = KalshiRequestSigner.from_config(config)
    return signer.build_auth_headers(method, request_path, timestamp_ms=timestamp_ms)
