from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from itertools import count
from typing import Any

import websockets
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_exponential
from websockets.asyncio.client import ClientConnection
from websockets.exceptions import ConnectionClosedError, InvalidStatus

from .auth import KalshiRequestSigner
from .config import KalshiClientConfig
from .exceptions import KalshiConfigurationError
from .models import WebSocketCommand, WebSocketMessage, WebSocketSubscriptionResponse


class KalshiWebSocketClient:
    def __init__(self, config: KalshiClientConfig) -> None:
        self.config = config
        private_key_pem = self.config.load_private_key_pem()
        if not (self.config.api_key_id and private_key_pem):
            raise KalshiConfigurationError("Kalshi WebSocket client requires API key ID and private key.")

        self.signer = KalshiRequestSigner(self.config.api_key_id, private_key_pem)
        self._connection: ClientConnection | None = None
        self._message_counter = count(1)

    async def connect(self) -> ClientConnection:
        headers = self.signer.build_headers("GET", "/trade-api/ws/v2")

        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(self.config.max_retries + 1),
            wait=wait_exponential(multiplier=0.5, min=0.5, max=8),
            retry=retry_if_exception_type((OSError, asyncio.TimeoutError, ConnectionClosedError, InvalidStatus)),
            reraise=True,
        ):
            with attempt:
                self._connection = await websockets.connect(
                    self.config.resolved_websocket_url,
                    additional_headers=headers,
                    ping_interval=20,
                    ping_timeout=20,
                    close_timeout=10,
                )

        return self._connection

    async def close(self) -> None:
        if self._connection is not None:
            await self._connection.close()
            self._connection = None

    async def __aenter__(self) -> "KalshiWebSocketClient":
        await self.connect()
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.close()

    async def send_command(self, cmd: str, params: dict[str, Any]) -> WebSocketCommand:
        if self._connection is None:
            await self.connect()

        message = WebSocketCommand(id=next(self._message_counter), cmd=cmd, params=params)
        assert self._connection is not None
        await self._connection.send(message.model_dump_json(exclude_none=True))
        return message

    async def subscribe(self, channels: list[str], market_tickers: list[str] | None = None) -> WebSocketCommand:
        params: dict[str, Any] = {"channels": channels}
        if market_tickers:
            params["market_tickers"] = market_tickers
        return await self.send_command("subscribe", params)

    async def unsubscribe(self, sids: list[int]) -> WebSocketCommand:
        return await self.send_command("unsubscribe", {"sids": sids})

    async def list_subscriptions(self) -> WebSocketCommand:
        return await self.send_command("list_subscriptions", {})

    async def update_subscription(
        self,
        sid: int,
        *,
        action: str,
        market_tickers: list[str],
    ) -> WebSocketCommand:
        return await self.send_command(
            "update_subscription",
            {
                "sids": [sid],
                "action": action,
                "market_tickers": market_tickers,
            },
        )

    async def recv(self) -> WebSocketSubscriptionResponse | WebSocketMessage:
        if self._connection is None:
            await self.connect()

        assert self._connection is not None
        raw = await self._connection.recv()
        data = json.loads(raw)

        if "cmd" in data or data.get("type") in {"subscribed", "unsubscribed", "ok", "error"}:
            return WebSocketSubscriptionResponse.model_validate(data)

        return WebSocketMessage.model_validate(data)

    async def iter_messages(self) -> AsyncIterator[WebSocketSubscriptionResponse | WebSocketMessage]:
        while True:
            yield await self.recv()
