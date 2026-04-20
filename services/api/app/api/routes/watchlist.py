from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_api_settings, get_db_session
from app.core.config import APISettings
from app.services.market_data import get_latest_snapshot, list_market_rows, serialize_market

from .markets import MarketReadResponse

router = APIRouter()


class WatchlistResponse(BaseModel):
    watchlist: list[str]
    markets: list[MarketReadResponse]


@router.get("", response_model=WatchlistResponse)
async def get_watchlist(
    settings: APISettings = Depends(get_api_settings),
    db: AsyncSession = Depends(get_db_session),
) -> WatchlistResponse:
    tickers = settings.watchlist_tickers
    rows = await list_market_rows(db, tickers=tickers or None)
    payload: list[MarketReadResponse] = []
    for row in rows:
        snapshot = await get_latest_snapshot(db, row.ticker)
        payload.append(MarketReadResponse.model_validate(serialize_market(row, snapshot)))
    return WatchlistResponse(watchlist=tickers, markets=payload)
