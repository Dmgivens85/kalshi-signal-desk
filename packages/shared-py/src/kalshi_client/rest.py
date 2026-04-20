from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

import httpx
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_exponential_jitter

from .auth import build_kalshi_auth_headers
from .config import KalshiClientConfig
from .errors import (
    KalshiApiError,
    KalshiAuthenticationError,
    KalshiFeatureDisabledError,
    KalshiNotFoundError,
    KalshiRateLimitError,
    KalshiTransportError,
)
from .models import (
    CancelOrderResponse,
    ExchangeStatus,
    EventResponse,
    GetMarketResponse,
    GetMarketsResponse,
    GetOrdersResponse,
    GetPositionsResponse,
    MarketResponse,
    MultipleOrderbooksResponse,
    OrderbookResponse,
    CreateOrderRequest,
    CreateOrderResponse,
    SeriesResponse,
)

logger = logging.getLogger(__name__)


def _filter_none(params: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if params is None:
        return None
    return {key: value for key, value in params.items() if value is not None}


class KalshiRestClient:
    def __init__(self, config: KalshiClientConfig, client: httpx.AsyncClient | None = None) -> None:
        self.config = config
        self.client = client or httpx.AsyncClient(
            base_url=self.config.resolved_api_base_url,
            timeout=httpx.Timeout(self.config.timeout_seconds),
        )

    async def __aenter__(self) -> "KalshiRestClient":
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        await self.client.aclose()

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json_body: Mapping[str, Any] | None = None,
        authenticated: bool = False,
    ) -> dict[str, Any]:
        headers: dict[str, str] = {}
        if authenticated:
            headers.update(build_kalshi_auth_headers(self.config, method, path))

        safe_params = _filter_none(params)
        logger.info("kalshi_rest_request", extra={"method": method, "path": path, "authenticated": authenticated})

        try:
            async for attempt in AsyncRetrying(
                stop=stop_after_attempt(self.config.max_retries + 1),
                wait=wait_exponential_jitter(initial=0.5, max=8),
                retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
                reraise=True,
            ):
                with attempt:
                    response = await self.client.request(
                        method=method,
                        url=path,
                        params=safe_params,
                        json=json_body,
                        headers=headers,
                    )
        except (httpx.TimeoutException, httpx.NetworkError) as exc:
            raise KalshiTransportError(f"Kalshi transport failure for {method} {path}") from exc

        if response.is_error:
            self._raise_for_error(response, method, path)

        if not response.content:
            return {}
        return response.json()

    def _raise_for_error(self, response: httpx.Response, method: str, path: str) -> None:
        try:
            payload = response.json()
        except ValueError:
            payload = {"detail": response.text}
        message = f"Kalshi request failed for {method} {path}"
        if response.status_code in {401, 403}:
            raise KalshiAuthenticationError(response.status_code, message, payload)
        if response.status_code == 404:
            raise KalshiNotFoundError(response.status_code, message, payload)
        if response.status_code == 429:
            raise KalshiRateLimitError(response.status_code, message, payload)
        raise KalshiApiError(response.status_code, message, payload)

    async def get_markets(
        self,
        *,
        limit: int | None = None,
        cursor: str | None = None,
        event_ticker: str | None = None,
        series_ticker: str | None = None,
        tickers: list[str] | None = None,
        status: str | None = None,
    ) -> GetMarketsResponse:
        payload = await self._request(
            "GET",
            "/markets",
            params={
                "limit": limit,
                "cursor": cursor,
                "event_ticker": event_ticker,
                "series_ticker": series_ticker,
                "tickers": tickers,
                "status": status,
            },
        )
        return GetMarketsResponse.model_validate(payload)

    async def get_market(self, ticker: str) -> GetMarketResponse:
        return GetMarketResponse.model_validate(await self._request("GET", f"/markets/{ticker}"))

    async def get_event(self, event_ticker: str) -> EventResponse:
        return EventResponse.model_validate(await self._request("GET", f"/events/{event_ticker}"))

    async def get_series(self, series_ticker: str) -> SeriesResponse:
        return SeriesResponse.model_validate(await self._request("GET", f"/series/{series_ticker}"))

    async def get_orderbook(self, ticker: str, *, depth: int | None = None) -> OrderbookResponse:
        return OrderbookResponse.model_validate(
            await self._request(
                "GET",
                f"/markets/{ticker}/orderbook",
                params={"depth": depth},
                authenticated=True,
            )
        )

    async def get_multiple_orderbooks(
        self,
        market_tickers: list[str],
        *,
        depth: int | None = None,
    ) -> MultipleOrderbooksResponse:
        return MultipleOrderbooksResponse.model_validate(
            await self._request(
                "GET",
                "/markets/orderbooks",
                params={"market_tickers": market_tickers, "depth": depth},
                authenticated=True,
            )
        )

    async def get_positions(self, *, cursor: str | None = None, limit: int | None = None) -> GetPositionsResponse:
        return GetPositionsResponse.model_validate(
            await self._request(
                "GET",
                "/portfolio/positions",
                params={"cursor": cursor, "limit": limit},
                authenticated=True,
            )
        )

    async def get_orders(self, *, cursor: str | None = None, limit: int | None = None) -> GetOrdersResponse:
        return GetOrdersResponse.model_validate(
            await self._request(
                "GET",
                "/portfolio/orders",
                params={"cursor": cursor, "limit": limit},
                authenticated=True,
            )
        )

    async def get_order(self, order_id: str) -> CreateOrderResponse:
        return CreateOrderResponse.model_validate(
            await self._request(
                "GET",
                f"/portfolio/orders/{order_id}",
                authenticated=True,
            )
        )

    async def get_exchange_status(self) -> ExchangeStatus:
        return ExchangeStatus.model_validate(await self._request("GET", "/exchange/status"))

    async def place_order(self, request: CreateOrderRequest) -> CreateOrderResponse:
        if not self.config.enable_trading:
            raise KalshiFeatureDisabledError(
                "Kalshi order placement is intentionally disabled in Phase 2."
            )
        return CreateOrderResponse.model_validate(
            await self._request(
                "POST",
                "/portfolio/orders",
                json_body=request.model_dump(mode="json", exclude_none=True),
                authenticated=True,
            )
        )

    async def create_order(self, request: CreateOrderRequest) -> CreateOrderResponse:
        return await self.place_order(request)

    async def cancel_order(self, order_id: str) -> CancelOrderResponse:
        return CancelOrderResponse.model_validate(
            await self._request(
                "DELETE",
                f"/portfolio/orders/{order_id}",
                authenticated=True,
            )
        )
