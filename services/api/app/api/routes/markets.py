from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.db.models import SignalRecord
from app.services.market_data import get_latest_snapshot, get_market_row, list_market_rows, serialize_market

router = APIRouter()


class MarketReadResponse(BaseModel):
    ticker: str
    event_ticker: str
    series_ticker: str | None = None
    title: str
    subtitle: str | None = None
    market_type: str | None = None
    status: str | None = None
    close_time: str | None = None
    last_price: int | None = None
    yes_bid: int | None = None
    yes_ask: int | None = None
    volume: int | None = None
    open_interest: int | None = None
    liquidity: int | None = None
    last_observed_at: str | None = None
    snapshot: dict[str, object] | None = None


class MarketListResponse(BaseModel):
    markets: list[MarketReadResponse]


class MarketSignalSummaryResponse(BaseModel):
    market_ticker: str
    signal: dict[str, object] | None = None


@router.get("", response_model=MarketListResponse)
async def list_markets(db: AsyncSession = Depends(get_db_session)) -> MarketListResponse:
    rows = await list_market_rows(db)
    payload: list[MarketReadResponse] = []
    for row in rows:
        snapshot = await get_latest_snapshot(db, row.ticker)
        payload.append(MarketReadResponse.model_validate(serialize_market(row, snapshot)))
    return MarketListResponse(markets=payload)


@router.get("/{ticker}/signal-summary", response_model=MarketSignalSummaryResponse)
async def get_market_signal_summary(ticker: str, db: AsyncSession = Depends(get_db_session)) -> MarketSignalSummaryResponse:
    result = await db.execute(
        select(SignalRecord).where(SignalRecord.market_ticker == ticker).order_by(desc(SignalRecord.created_at)).limit(1)
    )
    signal = result.scalar_one_or_none()
    return MarketSignalSummaryResponse(market_ticker=ticker, signal=signal.to_dict() if signal else None)


@router.get("/{ticker}", response_model=MarketReadResponse)
async def get_market(ticker: str, db: AsyncSession = Depends(get_db_session)) -> MarketReadResponse:
    row = await get_market_row(db, ticker)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Market not found: {ticker}")
    snapshot = await get_latest_snapshot(db, ticker)
    return MarketReadResponse.model_validate(serialize_market(row, snapshot))
