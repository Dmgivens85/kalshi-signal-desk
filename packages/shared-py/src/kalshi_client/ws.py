from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from itertools import count
from time import monotonic
from typing import Any

import websockets
from websockets.asyncio.client import ClientConnection
from websockets.exceptions import ConnectionClosed, InvalidStatus

from .auth import WS_SIGNING_PATH, build_kalshi_auth_headers
from .config import KalshiClientConfig
from .errors import KalshiTransportError
from .models import (
    ChannelName,
    NormalizedMarketEvent,
    OrderbookDelta,
    OrderbookSnapshot,
    TickerUpdate,
    WebSocketEnvelope,
)

logger = logging.getLogger(__name__)
EventHandler = Callable[[NormalizedMarketEvent], Awaitable[None]]


@dataclass(slots=True)
class SubscriptionRequest:
    channels: list[str]
    market_tickers: list[str] = field(default_factory=list)


class KalshiWebSocketClient:
    def __init__(self, config: KalshiClientConfig, event_handler: EventHandler) -> None:
        self.config = config
        self.event_handler = event_handler
        self.connection: ClientConnection | None = None
        self._message_ids = count(1)
        self._subscriptions: list[SubscriptionRequest] = []
        self._last_message_at = 0.0
        self._running = False

    async def connect(self) -> ClientConnection:
        headers = build_kalshi_auth_headers(self.config, "GET", WS_SIGNING_PATH)
        logger.info("kalshi_ws_connecting", extra={"url": self.config.resolved_ws_url})
        self.connection = await websockets.connect(
            self.config.resolved_ws_url,
            additional_headers=headers,
            open_timeout=self.config.connect_timeout_seconds,
            ping_interval=20,
            ping_timeout=20,
            close_timeout=10,
        )
        self._last_message_at = monotonic()
        logger.info("kalshi_ws_connected", extra={"url": self.config.resolved_ws_url})
        return self.connection

    async def close(self) -> None:
        self._running = False
        if self.connection is not None:
            await self.connection.close()
            self.connection = None

    async def subscribe(self, channels: list[str], market_tickers: list[str] | None = None) -> None:
        request = SubscriptionRequest(channels=channels, market_tickers=market_tickers or [])
        self._subscriptions.append(request)
        if self.connection is None:
            return
        await self._send_command(
            "subscribe",
            {"channels": channels, "market_tickers": market_tickers or None},
        )

    async def _send_command(self, cmd: str, params: dict[str, Any]) -> None:
        if self.connection is None:
            await self.connect()
        assert self.connection is not None
        payload = {"id": next(self._message_ids), "cmd": cmd, "params": params}
        await self.connection.send(json.dumps(payload))

    async def _resubscribe(self) -> None:
        for subscription in self._subscriptions:
            await self._send_command(
                "subscribe",
                {
                    "channels": subscription.channels,
                    "market_tickers": subscription.market_tickers or None,
                },
            )

    async def run_forever(self) -> None:
        self._running = True
        backoff = 1.0
        while self._running:
            try:
                await self.connect()
                await self._resubscribe()
                await self._consume()
                backoff = 1.0
            except (OSError, asyncio.TimeoutError, ConnectionClosed, InvalidStatus) as exc:
                logger.warning("kalshi_ws_connection_lost", extra={"error": str(exc), "backoff": backoff})
                await self.close()
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 30.0)
            except Exception as exc:
                logger.exception("kalshi_ws_unexpected_failure", extra={"error": str(exc)})
                await self.close()
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 30.0)

    async def _consume(self) -> None:
        assert self.connection is not None
        while self._running and self.connection is not None:
            try:
                raw_message = await asyncio.wait_for(
                    self.connection.recv(),
                    timeout=self.config.stale_after_seconds,
                )
            except TimeoutError as exc:
                raise KalshiTransportError("Kalshi websocket connection went stale.") from exc

            self._last_message_at = monotonic()
            envelope = WebSocketEnvelope.model_validate(json.loads(raw_message))
            normalized = self._normalize_envelope(envelope)
            if normalized is not None:
                await self.event_handler(normalized)

    def _normalize_envelope(self, envelope: WebSocketEnvelope) -> NormalizedMarketEvent | None:
        if envelope.type in {"subscribed", "unsubscribed", "ok"}:
            logger.info("kalshi_ws_subscription_event", extra={"type": envelope.type, "sid": envelope.sid})
            return None
        if envelope.type == "error":
            logger.warning("kalshi_ws_error", extra={"payload": envelope.msg})
            return None

        if envelope.type == ChannelName.TICKER:
            ticker = TickerUpdate.model_validate(envelope.msg)
            return NormalizedMarketEvent(
                event_type=ChannelName.TICKER,
                market_ticker=ticker.market_ticker,
                event_ticker=ticker.event_ticker,
                series_ticker=ticker.series_ticker,
                sequence_number=envelope.seq,
                subscription_id=envelope.sid,
                ticker_update=ticker,
                raw_payload=envelope.msg,
            )

        if envelope.type == ChannelName.ORDERBOOK_SNAPSHOT:
            snapshot = OrderbookSnapshot.model_validate(envelope.msg)
            return NormalizedMarketEvent(
                event_type=ChannelName.ORDERBOOK_SNAPSHOT,
                market_ticker=snapshot.market_ticker,
                sequence_number=envelope.seq,
                subscription_id=envelope.sid,
                orderbook_snapshot=snapshot,
                raw_payload=envelope.msg,
            )

        if envelope.type == ChannelName.ORDERBOOK_DELTA:
            delta = OrderbookDelta.model_validate(envelope.msg)
            return NormalizedMarketEvent(
                event_type=ChannelName.ORDERBOOK_DELTA,
                market_ticker=delta.market_ticker,
                sequence_number=envelope.seq,
                subscription_id=envelope.sid,
                orderbook_delta=delta,
                raw_payload=envelope.msg,
            )

        return None
