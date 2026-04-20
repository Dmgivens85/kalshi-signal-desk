from __future__ import annotations

from collections import defaultdict

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from kalshi_signal_shared import ExternalObservationModel, ExternalObservationType

from app.db.models import (
    ExternalEntityRecord,
    ExternalMarketMappingRecord,
    ExternalObservationRecord,
    ExternalSourceRecord,
    KalshiMarket,
    ServiceHealthEvent,
)
from external_enrichment.features import build_catalyst_candidates, build_consensus_feature


async def list_external_sources(db: AsyncSession) -> list[ExternalSourceRecord]:
    result = await db.execute(select(ExternalSourceRecord).order_by(ExternalSourceRecord.display_name.asc()))
    return list(result.scalars().all())


async def list_external_mappings(db: AsyncSession) -> list[ExternalMarketMappingRecord]:
    result = await db.execute(select(ExternalMarketMappingRecord).order_by(desc(ExternalMarketMappingRecord.updated_at)))
    return list(result.scalars().all())


async def get_external_health(db: AsyncSession) -> dict[str, object]:
    result = await db.execute(
        select(ServiceHealthEvent)
        .where(ServiceHealthEvent.service_name == "external-enrichment")
        .order_by(desc(ServiceHealthEvent.observed_at))
        .limit(10)
    )
    events = list(result.scalars().all())
    latest = events[0].status if events else "unknown"
    return {"status": latest, "events": [{"status": item.status, "observed_at": item.observed_at.isoformat()} for item in events]}


async def get_market_enrichment_summary(db: AsyncSession, ticker: str) -> dict[str, object]:
    mapping_rows = list(
        (
            await db.execute(
                select(ExternalMarketMappingRecord).where(
                    ExternalMarketMappingRecord.kalshi_market_ticker == ticker,
                    ExternalMarketMappingRecord.is_active.is_(True),
                )
            )
        ).scalars().all()
    )
    if not mapping_rows:
        return {"market_ticker": ticker, "sources": [], "features": None, "catalysts": []}

    entity_ids = [item.external_entity_row_id for item in mapping_rows]
    entity_rows = list(
        (await db.execute(select(ExternalEntityRecord).where(ExternalEntityRecord.id.in_(entity_ids)))).scalars().all()
    )
    entities_by_row_id = {item.id: item for item in entity_rows}
    observations = list(
        (
            await db.execute(
                select(ExternalObservationRecord).where(ExternalObservationRecord.external_entity_row_id.in_(entity_ids))
            )
        ).scalars().all()
    )
    observations_by_row_id: dict[str, list[ExternalObservationRecord]] = defaultdict(list)
    for observation in observations:
        observations_by_row_id[observation.external_entity_row_id].append(observation)

    normalized_observations = [
        ExternalObservationModel(
            source_slug="db",
            external_entity_id=observation.external_entity_id,
            observation_type=ExternalObservationType(observation.observation_type),
            observed_at=observation.observed_at,
            probability_value=observation.probability_value,
            numeric_value=observation.numeric_value,
            title=observation.title,
            summary=observation.summary,
            url=observation.url,
            tags=observation.tags,
            entities=observation.entities,
            raw_text_available=observation.raw_text_available,
            ai_metadata=observation.ai_metadata,
            raw_payload=observation.raw_payload,
        )
        for observation in observations
    ]
    market = await db.get(KalshiMarket, ticker)
    kalshi_probability = ((market.last_price or market.yes_bid or market.yes_ask or 50) / 100.0) if market else 0.5
    feature = build_consensus_feature(
        kalshi_market_ticker=ticker,
        kalshi_probability=kalshi_probability,
        observations=normalized_observations,
    )
    catalysts = build_catalyst_candidates(normalized_observations)

    sources: list[dict[str, object]] = []
    for mapping in mapping_rows:
        entity = entities_by_row_id.get(mapping.external_entity_row_id)
        entity_observations = observations_by_row_id.get(mapping.external_entity_row_id, [])
        sources.append(
            {
                "mapping": mapping.to_dict(),
                "entity": entity.to_dict() if entity else None,
                "observations": [item.to_dict() for item in entity_observations],
            }
        )

    return {
        "market_ticker": ticker,
        "sources": sources,
        "features": feature.model_dump(mode="json"),
        "catalysts": [item.model_dump(mode="json") for item in catalysts],
    }
