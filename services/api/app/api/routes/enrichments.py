from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_api_settings, get_db_session, require_auth
from app.core.auth import AuthContext
from app.core.config import APISettings
from app.db.models import ExternalEntityRecord, ExternalMarketMappingRecord
from app.services.enrichment_reader import get_external_health, get_market_enrichment_summary, list_external_mappings, list_external_sources
from external_enrichment.config import ExternalEnrichmentSettings
from external_enrichment.scheduler import EnrichmentScheduler

router = APIRouter()


class MappingOverrideRequest(BaseModel):
    external_entity_row_id: str
    kalshi_market_ticker: str
    source_notes: str


@router.get("/providers")
async def list_providers(db: AsyncSession = Depends(get_db_session)) -> dict[str, object]:
    rows = await list_external_sources(db)
    return {"providers": [row.slug for row in rows]}


@router.post("/sync")
async def sync_enrichments(
    _: AuthContext = Depends(require_auth),
    settings: APISettings = Depends(get_api_settings),
) -> dict[str, object]:
    scheduler = EnrichmentScheduler(
        ExternalEnrichmentSettings(
            database_url=settings.database_url,
            redis_url=settings.redis_url,
            sportsbook_primary_url=settings.sportsbook_odds_api_url,
            polymarket_api_url=settings.polymarket_api_url,
            metaculus_api_url=settings.metaculus_api_url,
            manifold_api_url=settings.manifold_api_url,
            news_api_url=settings.news_api_url,
            news_api_key=settings.news_api_key,
            watchlist_tickers=",".join(settings.watchlist_tickers),
        )
    )
    try:
        return await scheduler.run_once()
    finally:
        await scheduler.worker.aclose()


@router.get("/sources")
async def get_sources(db: AsyncSession = Depends(get_db_session)) -> dict[str, object]:
    rows = await list_external_sources(db)
    return {"items": [item.to_dict() for item in rows]}


@router.get("/mappings")
async def get_mappings(db: AsyncSession = Depends(get_db_session)) -> dict[str, object]:
    rows = await list_external_mappings(db)
    return {"items": [item.to_dict() for item in rows]}


@router.get("/markets/{ticker}/summary")
async def get_market_summary(ticker: str, db: AsyncSession = Depends(get_db_session)) -> dict[str, object]:
    return await get_market_enrichment_summary(db, ticker)


@router.get("/health")
async def get_health(db: AsyncSession = Depends(get_db_session)) -> dict[str, object]:
    return await get_external_health(db)


@router.post("/mappings/override", status_code=status.HTTP_201_CREATED)
async def create_mapping_override(
    payload: MappingOverrideRequest,
    _: AuthContext = Depends(require_auth),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    entity = await db.get(ExternalEntityRecord, payload.external_entity_row_id)
    if entity is None:
        raise HTTPException(status_code=404, detail="External entity not found.")
    override = ExternalMarketMappingRecord(
        external_entity_row_id=payload.external_entity_row_id,
        external_entity_id=entity.external_id if entity else payload.external_entity_row_id,
        kalshi_market_ticker=payload.kalshi_market_ticker,
        confidence_score=1.0,
        strategy="manual_override",
        source_notes=payload.source_notes,
        manual_override=True,
        is_active=True,
    )
    db.add(override)
    await db.commit()
    await db.refresh(override)
    return override.to_dict()
