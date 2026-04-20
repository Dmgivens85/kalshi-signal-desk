from __future__ import annotations

import base64
import time
from pathlib import Path
from urllib.parse import urlsplit

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from .exceptions import KalshiConfigurationError


def _normalize_signing_path(path: str) -> str:
    return path.split("?", 1)[0]


class KalshiRequestSigner:
    def __init__(self, api_key_id: str, private_key_pem: str) -> None:
        if not api_key_id:
            raise KalshiConfigurationError("Kalshi API key ID is required for authenticated requests.")
        if not private_key_pem:
            raise KalshiConfigurationError("Kalshi private key PEM is required for authenticated requests.")

        self.api_key_id = api_key_id
        self.private_key = serialization.load_pem_private_key(
            private_key_pem.encode("utf-8"),
            password=None,
        )

        if not isinstance(self.private_key, rsa.RSAPrivateKey):
            raise KalshiConfigurationError("Kalshi private key must be an RSA private key.")

    @classmethod
    def from_file(cls, api_key_id: str, path: str | Path) -> "KalshiRequestSigner":
        return cls(api_key_id=api_key_id, private_key_pem=Path(path).read_text(encoding="utf-8"))

    def sign_message(self, timestamp_ms: str, method: str, path: str) -> str:
        payload = f"{timestamp_ms}{method.upper()}{_normalize_signing_path(path)}".encode("utf-8")
        signature = self.private_key.sign(
            payload,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.DIGEST_LENGTH,
            ),
            hashes.SHA256(),
        )
        return base64.b64encode(signature).decode("utf-8")

    def build_headers(
        self,
        method: str,
        path: str,
        timestamp_ms: str | None = None,
    ) -> dict[str, str]:
        ts = timestamp_ms or str(int(time.time() * 1000))
        return {
            "KALSHI-ACCESS-KEY": self.api_key_id,
            "KALSHI-ACCESS-TIMESTAMP": ts,
            "KALSHI-ACCESS-SIGNATURE": self.sign_message(ts, method, path),
        }

    def build_headers_for_url(self, method: str, url: str, timestamp_ms: str | None = None) -> dict[str, str]:
        parsed = urlsplit(url)
        path = parsed.path or "/"
        if parsed.query:
            path = f"{path}?{parsed.query}"
        return self.build_headers(method=method, path=path, timestamp_ms=timestamp_ms)
