class KalshiError(Exception):
    """Base error for Kalshi client operations."""


class KalshiConfigurationError(KalshiError):
    """Raised when the client is missing required configuration."""


class KalshiApiError(KalshiError):
    def __init__(self, status_code: int, message: str, payload: object | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload
