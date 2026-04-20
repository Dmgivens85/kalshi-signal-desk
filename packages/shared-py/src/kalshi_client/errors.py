from __future__ import annotations

from typing import Any


class KalshiClientError(Exception):
    """Base error for Kalshi client failures."""


class KalshiConfigurationError(KalshiClientError):
    """Raised when required configuration is missing or invalid."""


class KalshiSigningError(KalshiClientError):
    """Raised when request signing cannot be completed."""


class KalshiApiError(KalshiClientError):
    """Raised when the Kalshi REST API returns an error response."""

    def __init__(self, status_code: int, message: str, payload: Any | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload


class KalshiAuthenticationError(KalshiApiError):
    """Raised for authentication or authorization failures."""


class KalshiRateLimitError(KalshiApiError):
    """Raised when Kalshi rate limits a request."""


class KalshiNotFoundError(KalshiApiError):
    """Raised when a requested resource is not found."""


class KalshiTransportError(KalshiClientError):
    """Raised for transient HTTP or websocket transport failures."""


class KalshiFeatureDisabledError(KalshiClientError):
    """Raised when a potentially dangerous feature is intentionally disabled."""
