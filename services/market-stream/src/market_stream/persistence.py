from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.models import KalshiMarket, MarketSnapshot, OrderbookEvent, ServiceHealthEvent
from kalshi_client import MarketModel, NormalizedMarketEvent, OrderbookSnapshot


class MarketStreamPersistence:
    def __init__(self, database_url: str, redis_url: str | None = None, *, cache_latest_state: bool = True) -> None:
        self.engine = create_async_engine(database_url, future=True)
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False, class_=AsyncSession)
        self.redis = Redis.from_url(redis_url) if redis_url and cache_latest_state else None

    async def aclose(self) -> None:
        await self.engine.dispose()
        if self.redis is not None:
            await self.redis.aclose()

    async def upsert_market(self, market: MarketModel, *, observed_at: datetime | None = None) -> None:
        async with self.session_factory() as session:
            row = await session.get(KalshiMarket, market.ticker)
            if row is None:
                row = KalshiMarket(
                    ticker=market.ticker,
                    event_ticker=market.event_ticker,
                    series_ticker=market.series_ticker,
                    title=market.title,
                    subtitle=market.subtitle,
                    market_type=market.market_type,
                    status=market.status,
                    close_time=market.close_time,
                    last_price=market.last_price,
                    yes_bid=market.yes_bid,
                    yes_ask=market.yes_ask,
                    volume=market.volume,
                    open_interest=market.open_interest,
                    liquidity=market.liquidity,
                    last_observed_at=observed_at,
                    raw_payload=market.raw or market.model_dump(mode="json"),
                )
                session.add(row)
            else:
                row.event_ticker = market.event_ticker
                row.series_ticker = market.series_ticker
                row.title = market.title
                row.subtitle = market.subtitle
                row.market_type = market.market_type
                row.status = market.status
                row.close_time = market.close_time
                row.last_price = market.last_price
                row.yes_bid = market.yes_bid
                row.yes_ask = market.yes_ask
                row.volume = market.volume
                row.open_interest = market.open_interest
                row.liquidity = market.liquidity
                row.last_observed_at = observed_at
                row.raw_payload = market.raw or market.model_dump(mode="json")
            await session.commit()

    async def store_snapshot(
        self,
        *,
        market: KalshiMarket,
        snapshot_type: str,
        observed_at: datetime,
        sequence_number: int | None,
        bid_levels: list[dict[str, Any]] | None = None,
        ask_levels: list[dict[str, Any]] | None = None,
        raw_payload: dict[str, Any],
    ) -> None:
        async with self.session_factory() as session:
            session.add(
                MarketSnapshot(
                    market_ticker=market.ticker,
                    event_ticker=market.event_ticker,
                    title=market.title,
                    status=market.status or "unknown",
                    close_time=market.close_time,
                    last_price=market.last_price,
                    yes_bid=market.yes_bid,
                    yes_ask=market.yes_ask,
                    volume=market.volume,
                    open_interest=market.open_interest,
                    snapshot_type=snapshot_type,
                    sequence_number=sequence_number,
                    observed_at=observed_at,
                    bid_levels=bid_levels or [],
                    ask_levels=ask_levels or [],
                    raw_payload=raw_payload,
                )
            )
            await session.commit()

    async def record_orderbook_event(self, event: NormalizedMarketEvent) -> None:
        async with self.session_factory() as session:
            bid_levels = event.orderbook_snapshot.yes if event.orderbook_snapshot else []
            ask_levels = event.orderbook_snapshot.no if event.orderbook_snapshot else []
            session.add(
                OrderbookEvent(
                    market_ticker=event.market_ticker,
                    event_type=str(event.event_type),
                    sequence_number=event.sequence_number,
                    side=event.orderbook_delta.side if event.orderbook_delta else None,
                    price=event.orderbook_delta.price if event.orderbook_delta else None,
                    delta=event.orderbook_delta.delta if event.orderbook_delta else None,
                    observed_at=event.observed_at,
                    bid_levels=[level.model_dump(mode="json") for level in bid_levels],
                    ask_levels=[level.model_dump(mode="json") for level in ask_levels],
                    raw_payload=event.raw_payload,
                )
            )
            await session.commit()

    async def record_service_health(self, service_name: str, status: str, *, detail: str | None = None) -> None:
        async with self.session_factory() as session:
            session.add(
                ServiceHealthEvent(
                    service_name=service_name,
                    status=status,
                    detail=detail,
                    payload={},
                )
            )
            await session.commit()

        if self.redis is not None:
            await self.redis.set(
                f"service-health:{service_name}",
                json.dumps({"status": status, "detail": detail}),
                ex=120,
            )

    async def load_market(self, ticker: str) -> KalshiMarket | None:
        async with self.session_factory() as session:
            return await session.get(KalshiMarket, ticker)

    async def ensure_market_stub(self, ticker: str, *, event_ticker: str | None = None) -> KalshiMarket:
        async with self.session_factory() as session:
            row = await session.get(KalshiMarket, ticker)
            if row is None:
                row = KalshiMarket(
                    ticker=ticker,
                    event_ticker=event_ticker or ticker,
                    title=ticker,
                    status="unknown",
                    raw_payload={},
                )
                session.add(row)
                await session.commit()
            return row

    async def cache_latest_state(self, ticker: str, payload: dict[str, Any]) -> None:
        if self.redis is None:
            return
        await self.redis.set(f"kalshi:latest:{ticker}", json.dumps(payload), ex=3600)
