from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

import httpx
from pydantic import BaseModel
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_exponential

from .auth import KalshiRequestSigner
from .config import KalshiClientConfig
from .exceptions import KalshiApiError, KalshiConfigurationError
from .models import (
    CreateOrderRequest,
    CreateOrderResponse,
    ExchangeStatus,
    GetBalanceResponse,
    GetFillsResponse,
    GetMarketResponse,
    GetMarketsResponse,
    GetOrdersResponse,
    GetPositionsResponse,
    QueuePositionsResponse,
)

ResponseModelT = TypeVar("ResponseModelT", bound=BaseModel)


class KalshiHttpClient:
    def __init__(self, config: KalshiClientConfig, client: httpx.AsyncClient | None = None) -> None:
        self.config = config
        self.client = client or httpx.AsyncClient(
            base_url=self.config.resolved_base_url,
            timeout=self.config.request_timeout_seconds,
        )
        private_key_pem = self.config.load_private_key_pem()
        self.signer = (
            KalshiRequestSigner(api_key_id=self.config.api_key_id, private_key_pem=private_key_pem)
            if self.config.api_key_id and private_key_pem
            else None
        )

    async def aclose(self) -> None:
        await self.client.aclose()

    async def __aenter__(self) -> "KalshiHttpClient":
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.aclose()

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json: Mapping[str, Any] | None = None,
        authenticated: bool = False,
    ) -> dict[str, Any]:
        headers: dict[str, str] = {}
        if authenticated:
            if self.signer is None:
                raise KalshiConfigurationError("Authenticated Kalshi request requires API key and private key.")
            headers.update(self.signer.build_headers(method, path))

        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(self.config.max_retries + 1),
            wait=wait_exponential(multiplier=0.5, min=0.5, max=4),
            retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
            reraise=True,
        ):
            with attempt:
                response = await self.client.request(
                    method=method,
                    url=path,
                    params=params,
                    json=json,
                    headers=headers,
                )

        if response.is_error:
            try:
                payload = response.json()
            except ValueError:
                payload = response.text
            raise KalshiApiError(response.status_code, f"Kalshi request failed for {method} {path}", payload)

        if not response.content:
            return {}

        return response.json()

    async def request_model(
        self,
        method: str,
        path: str,
        model: type[ResponseModelT],
        *,
        params: Mapping[str, Any] | None = None,
        json: Mapping[str, Any] | None = None,
        authenticated: bool = False,
    ) -> ResponseModelT:
        payload = await self.request(method, path, params=params, json=json, authenticated=authenticated)
        return model.model_validate(payload)

    async def get_exchange_status(self) -> ExchangeStatus:
        return await self.request_model("GET", "/exchange/status", ExchangeStatus)

    async def get_markets(self, *, params: Mapping[str, Any] | None = None) -> GetMarketsResponse:
        return await self.request_model("GET", "/markets", GetMarketsResponse, params=params)

    async def get_market(self, ticker: str) -> GetMarketResponse:
        return await self.request_model("GET", f"/markets/{ticker}", GetMarketResponse)

    async def get_balance(self, *, subaccount: int | None = None) -> GetBalanceResponse:
        params = {"subaccount": subaccount} if subaccount is not None else None
        return await self.request_model(
            "GET",
            "/portfolio/balance",
            GetBalanceResponse,
            params=params,
            authenticated=True,
        )

    async def get_positions(self, *, params: Mapping[str, Any] | None = None) -> GetPositionsResponse:
        return await self.request_model(
            "GET",
            "/portfolio/positions",
            GetPositionsResponse,
            params=params,
            authenticated=True,
        )

    async def get_orders(self, *, params: Mapping[str, Any] | None = None) -> GetOrdersResponse:
        return await self.request_model(
            "GET",
            "/portfolio/orders",
            GetOrdersResponse,
            params=params,
            authenticated=True,
        )

    async def create_order(self, request: CreateOrderRequest) -> CreateOrderResponse:
        return await self.request_model(
            "POST",
            "/portfolio/orders",
            CreateOrderResponse,
            json=request.model_dump(mode="json", exclude_none=True),
            authenticated=True,
        )

    async def get_fills(self, *, params: Mapping[str, Any] | None = None) -> GetFillsResponse:
        return await self.request_model(
            "GET",
            "/portfolio/fills",
            GetFillsResponse,
            params=params,
            authenticated=True,
        )

    async def get_queue_positions(self, *, params: Mapping[str, Any] | None = None) -> QueuePositionsResponse:
        return await self.request_model(
            "GET",
            "/portfolio/orders/queue_positions",
            QueuePositionsResponse,
            params=params,
            authenticated=True,
        )
