from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import delete, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    AlertEventRecord,
    ExternalMarketMappingRecord,
    KalshiMarket,
    MarketSnapshot,
    OrderbookEvent,
    SignalFeatureRecord,
    SignalRecord,
    StrategyRecord,
)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class SignalRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def load_markets(self) -> list[KalshiMarket]:
        return list((await self.db.execute(select(KalshiMarket).order_by(desc(KalshiMarket.last_observed_at)))).scalars().all())

    async def load_market_snapshots(self, ticker: str, limit: int = 12) -> list[MarketSnapshot]:
        result = await self.db.execute(
            select(MarketSnapshot)
            .where(MarketSnapshot.market_ticker == ticker)
            .order_by(desc(MarketSnapshot.observed_at))
            .limit(limit)
        )
        return list(result.scalars().all())[::-1]

    async def load_orderbook_events(self, ticker: str, limit: int = 50) -> list[OrderbookEvent]:
        result = await self.db.execute(
            select(OrderbookEvent)
            .where(OrderbookEvent.market_ticker == ticker)
            .order_by(desc(OrderbookEvent.observed_at))
            .limit(limit)
        )
        return list(result.scalars().all())[::-1]

    async def load_external_mappings(self, ticker: str) -> list[ExternalMarketMappingRecord]:
        result = await self.db.execute(
            select(ExternalMarketMappingRecord)
            .where(
                ExternalMarketMappingRecord.kalshi_market_ticker == ticker,
                ExternalMarketMappingRecord.is_active.is_(True),
            )
            .order_by(desc(ExternalMarketMappingRecord.updated_at))
        )
        return list(result.scalars().all())

    async def get_or_create_strategy(self, slug: str, *, name: str, description: str, config_json: dict[str, Any]) -> StrategyRecord:
        row = (await self.db.execute(select(StrategyRecord).where(StrategyRecord.slug == slug))).scalar_one_or_none()
        if row is None:
            row = StrategyRecord(slug=slug, name=name, description=description, config_json=config_json)
            self.db.add(row)
            await self.db.flush()
        else:
            row.name = name
            row.description = description
            row.config_json = config_json
        return row

    async def replace_signal(self, signal: SignalRecord, features: list[SignalFeatureRecord], alert_event: AlertEventRecord | None) -> SignalRecord:
        existing = (
            await self.db.execute(
                select(SignalRecord).where(
                    SignalRecord.market_ticker == signal.market_ticker,
                    SignalRecord.dedupe_key == signal.dedupe_key,
                )
            )
        ).scalar_one_or_none()
        if existing is not None:
            await self.db.execute(delete(SignalFeatureRecord).where(SignalFeatureRecord.signal_id == existing.id))
            await self.db.delete(existing)
            await self.db.flush()

        self.db.add(signal)
        await self.db.flush()
        for feature in features:
            feature.signal_id = signal.id
            self.db.add(feature)
        if alert_event is not None:
            alert_event.signal_id = signal.id
            self.db.add(alert_event)
        return signal

    async def load_recent_alerts(self, *, dedupe_key: str, since: datetime) -> list[AlertEventRecord]:
        result = await self.db.execute(
            select(AlertEventRecord)
            .where(AlertEventRecord.dedupe_key == dedupe_key, AlertEventRecord.created_at >= since)
            .order_by(desc(AlertEventRecord.created_at))
        )
        return list(result.scalars().all())

    async def seed_demo_data(self) -> None:
        if await self.load_markets():
            return
        demo_close = utcnow() + timedelta(days=14)
        markets = [
            KalshiMarket(
                ticker="FED-2026-CUTS",
                event_ticker="FED-2026",
                title="Will the Fed deliver a rate cut by June 2026?",
                status="open",
                last_price=58,
                yes_bid=57,
                yes_ask=59,
                volume=18420,
                open_interest=7220,
                liquidity=16000,
                close_time=demo_close,
                last_observed_at=utcnow(),
                raw_payload={},
            ),
            KalshiMarket(
                ticker="US-RECESSION-2026",
                event_ticker="MACRO-2026",
                title="Will the US enter recession in 2026?",
                status="open",
                last_price=48,
                yes_bid=47,
                yes_ask=49,
                volume=12100,
                open_interest=6110,
                liquidity=11000,
                close_time=demo_close,
                last_observed_at=utcnow(),
                raw_payload={},
            ),
        ]
        for market in markets:
            self.db.add(market)
            for step, price in enumerate([market.last_price - 4, market.last_price - 2, market.last_price]):
                self.db.add(
                    MarketSnapshot(
                        market_ticker=market.ticker,
                        event_ticker=market.event_ticker,
                        title=market.title,
                        status=market.status or "open",
                        close_time=market.close_time,
                        last_price=price,
                        yes_bid=max(1, price - 1),
                        yes_ask=min(99, price + 1),
                        volume=market.volume - 500 + (step * 250),
                        open_interest=market.open_interest,
                        snapshot_type="ticker",
                        sequence_number=step + 1,
                        observed_at=utcnow() - timedelta(minutes=(15 - step * 5)),
                        bid_levels=[],
                        ask_levels=[],
                        raw_payload={},
                    )
                )
        await self.db.flush()

    async def list_signals(self) -> list[SignalRecord]:
        return list((await self.db.execute(select(SignalRecord).order_by(desc(SignalRecord.created_at)))).scalars().all())

    async def get_signal(self, signal_id: str) -> SignalRecord | None:
        return await self.db.get(SignalRecord, signal_id)

    async def get_signal_features(self, signal_id: str) -> list[SignalFeatureRecord]:
        result = await self.db.execute(
            select(SignalFeatureRecord)
            .where(SignalFeatureRecord.signal_id == signal_id)
            .order_by(SignalFeatureRecord.feature_group, desc(SignalFeatureRecord.feature_value))
        )
        return list(result.scalars().all())

    async def market_latest_signal(self, ticker: str) -> SignalRecord | None:
        result = await self.db.execute(
            select(SignalRecord).where(SignalRecord.market_ticker == ticker).order_by(desc(SignalRecord.created_at)).limit(1)
        )
        return result.scalar_one_or_none()
