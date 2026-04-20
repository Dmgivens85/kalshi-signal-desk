from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from sqlalchemy import Select, desc, select
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import KalshiMarket, MarketSnapshot


async def list_market_rows(db: AsyncSession, *, tickers: Sequence[str] | None = None) -> list[KalshiMarket]:
    query: Select[tuple[KalshiMarket]] = select(KalshiMarket).order_by(desc(KalshiMarket.last_observed_at))
    if tickers:
        query = query.where(KalshiMarket.ticker.in_(list(tickers)))
    try:
        result = await db.execute(query)
    except OperationalError:
        return []
    return list(result.scalars().all())


async def get_market_row(db: AsyncSession, ticker: str) -> KalshiMarket | None:
    try:
        return await db.get(KalshiMarket, ticker)
    except OperationalError:
        return None


async def get_latest_snapshot(db: AsyncSession, ticker: str) -> MarketSnapshot | None:
    try:
        result = await db.execute(
            select(MarketSnapshot)
            .where(MarketSnapshot.market_ticker == ticker)
            .order_by(desc(MarketSnapshot.observed_at))
            .limit(1)
        )
    except OperationalError:
        return None
    return result.scalar_one_or_none()


def serialize_market(market: KalshiMarket, snapshot: MarketSnapshot | None = None) -> dict[str, Any]:
    payload = market.to_dict()
    payload["snapshot"] = snapshot.to_dict() if snapshot else None
    return payload
