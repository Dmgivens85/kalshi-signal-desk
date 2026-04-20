from __future__ import annotations

import asyncio
import logging
from contextlib import suppress

from kalshi_client import (
    ChannelName,
    KalshiRestClient,
    KalshiWebSocketClient,
    MarketModel,
    NormalizedMarketEvent,
)

from .config import MarketStreamSettings
from .persistence import MarketStreamPersistence

logger = logging.getLogger(__name__)


class MarketStreamService:
    def __init__(self, settings: MarketStreamSettings) -> None:
        self.settings = settings
        self.persistence = MarketStreamPersistence(
            database_url=settings.database_url,
            redis_url=settings.redis_url,
            cache_latest_state=settings.cache_latest_state,
        )
        self.ws_client = KalshiWebSocketClient(settings.build_kalshi_config(), self.handle_event)
        self._heartbeat_task: asyncio.Task[None] | None = None

    async def bootstrap_watchlist(self) -> None:
        if not self.settings.bootstrap_rest_on_startup or not self.settings.watchlist_tickers:
            return

        async with KalshiRestClient(self.settings.build_kalshi_config()) as client:
            for ticker in self.settings.watchlist_tickers:
                try:
                    market_response = await client.get_market(ticker)
                    market = market_response.market
                    await self.persistence.upsert_market(market, observed_at=market.close_time)
                except Exception as exc:
                    logger.warning("market_stream_bootstrap_market_failed", extra={"ticker": ticker, "error": str(exc)})

            try:
                orderbooks = await client.get_multiple_orderbooks(self.settings.watchlist_tickers)
            except Exception as exc:
                logger.warning("market_stream_bootstrap_orderbooks_failed", extra={"error": str(exc)})
                return

            for snapshot in orderbooks.orderbooks:
                row = await self.persistence.ensure_market_stub(snapshot.market_ticker)
                await self.persistence.store_snapshot(
                    market=row,
                    snapshot_type="bootstrap_orderbook",
                    observed_at=snapshot.ts or row.last_observed_at or row.created_at,
                    sequence_number=None,
                    bid_levels=[level.model_dump(mode="json") for level in snapshot.yes],
                    ask_levels=[level.model_dump(mode="json") for level in snapshot.no],
                    raw_payload=snapshot.model_dump(mode="json"),
                )

    async def start(self) -> None:
        await self.persistence.record_service_health(self.settings.service_name, "starting")
        await self.bootstrap_watchlist()
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

        if self.settings.watchlist_tickers:
            await self.ws_client.subscribe([ChannelName.TICKER], self.settings.watchlist_tickers)
            await self.ws_client.subscribe([ChannelName.ORDERBOOK_DELTA], self.settings.watchlist_tickers)
        else:
            await self.ws_client.subscribe([ChannelName.TICKER])

        await self.persistence.record_service_health(self.settings.service_name, "running")
        await self.ws_client.run_forever()

    async def stop(self) -> None:
        if self._heartbeat_task is not None:
            self._heartbeat_task.cancel()
            with suppress(asyncio.CancelledError):
                await self._heartbeat_task
        await self.ws_client.close()
        await self.persistence.record_service_health(self.settings.service_name, "stopped")
        await self.persistence.aclose()

    async def _heartbeat_loop(self) -> None:
        while True:
            await self.persistence.record_service_health(self.settings.service_name, "healthy")
            await asyncio.sleep(self.settings.heartbeat_interval_seconds)

    async def handle_event(self, event: NormalizedMarketEvent) -> None:
        if event.ticker_update is not None:
            market = await self._upsert_from_ticker(event)
            await self.persistence.store_snapshot(
                market=market,
                snapshot_type="ticker",
                observed_at=event.observed_at,
                sequence_number=event.sequence_number,
                raw_payload=event.raw_payload,
            )
            await self.persistence.cache_latest_state(
                event.market_ticker,
                {
                    "type": "ticker",
                    "payload": event.ticker_update.model_dump(mode="json"),
                    "observed_at": event.observed_at.isoformat(),
                },
            )
            return

        if event.orderbook_snapshot is not None:
            market = await self.persistence.ensure_market_stub(event.market_ticker)
            await self.persistence.record_orderbook_event(event)
            await self.persistence.store_snapshot(
                market=market,
                snapshot_type="orderbook_snapshot",
                observed_at=event.observed_at,
                sequence_number=event.sequence_number,
                bid_levels=[level.model_dump(mode="json") for level in event.orderbook_snapshot.yes],
                ask_levels=[level.model_dump(mode="json") for level in event.orderbook_snapshot.no],
                raw_payload=event.raw_payload,
            )
            return

        if event.orderbook_delta is not None:
            await self.persistence.ensure_market_stub(event.market_ticker)
            await self.persistence.record_orderbook_event(event)
            await self.persistence.cache_latest_state(
                event.market_ticker,
                {
                    "type": "orderbook_delta",
                    "payload": event.orderbook_delta.model_dump(mode="json"),
                    "observed_at": event.observed_at.isoformat(),
                },
            )

    async def _upsert_from_ticker(self, event: NormalizedMarketEvent):
        ticker = event.ticker_update
        assert ticker is not None
        market = MarketModel(
            ticker=ticker.market_ticker,
            event_ticker=ticker.event_ticker or ticker.market_ticker,
            series_ticker=ticker.series_ticker,
            title=ticker.market_ticker,
            status=ticker.status,
            yes_bid=ticker.yes_bid,
            yes_ask=ticker.yes_ask,
            last_price=ticker.last_price,
            volume=ticker.volume,
            open_interest=ticker.open_interest,
            liquidity=ticker.liquidity,
            raw=ticker.model_dump(mode="json"),
        )
        await self.persistence.upsert_market(market, observed_at=event.observed_at)
        row = await self.persistence.load_market(market.ticker)
        if row is None:
            row = await self.persistence.ensure_market_stub(market.ticker, event_ticker=market.event_ticker)
        return row
