from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone

from redis.asyncio import Redis
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from kalshi_signal_shared import ExternalEntityModel, ExternalObservationModel

from app.db.models import (
    ExternalEntityRecord,
    ExternalMarketMappingRecord,
    ExternalObservationRecord,
    ExternalSourceRecord,
    KalshiMarket,
    ServiceHealthEvent,
)
from external_enrichment.config import ExternalEnrichmentSettings
from external_enrichment.features import build_catalyst_candidates, build_consensus_feature
from external_enrichment.mappers import MappingEngine
from external_enrichment.providers import (
    ManifoldAdapter,
    MetaculusAdapter,
    NewsProviderAdapter,
    PolymarketAdapter,
    SportsbookPrimaryAdapter,
    SportsbookSecondaryAdapter,
)


class ExternalEnrichmentWorker:
    def __init__(self, settings: ExternalEnrichmentSettings) -> None:
        self.settings = settings
        self.engine = create_async_engine(settings.database_url, future=True)
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False, class_=AsyncSession)
        self.redis = Redis.from_url(settings.redis_url)
        self.mapping_engine = MappingEngine()
        self.providers = [
            SportsbookPrimaryAdapter(settings),
            SportsbookSecondaryAdapter(settings),
            PolymarketAdapter(settings),
            MetaculusAdapter(settings),
            ManifoldAdapter(settings),
            NewsProviderAdapter(settings),
        ]

    async def aclose(self) -> None:
        await self.engine.dispose()
        await self.redis.aclose()

    async def run_once(self) -> dict[str, object]:
        async with self.session_factory() as session:
            await self._record_health(session, "running")
            source_rows = await self._upsert_sources(session)
            kalshi_markets = list((await session.execute(select(KalshiMarket))).scalars().all())
            existing_overrides = list(
                (
                    await session.execute(
                        select(ExternalMarketMappingRecord).where(ExternalMarketMappingRecord.manual_override.is_(True))
                    )
                ).scalars().all()
            )

            provider_counts: dict[str, int] = {}
            all_observations_by_market: dict[str, list[ExternalObservationModel]] = defaultdict(list)

            for provider in self.providers:
                source_row = source_rows[provider.source.slug]
                entities = await provider.fetch_markets_or_questions()
                observations = await provider.fetch_observations(entities)
                entities, observations = await provider.normalize(entities, observations)
                source_row.status = "healthy"
                source_row.last_synced_at = datetime.now(timezone.utc)
                source_row.last_error = None
                provider_counts[provider.source.slug] = len(entities)
                entity_rows = await self._upsert_entities(session, source_row.id, entities)
                await self._replace_observations(session, source_row.id, entity_rows, observations)
                mappings = await self._refresh_mappings(session, entities, entity_rows, kalshi_markets, existing_overrides)
                for mapping in mappings:
                    entity_obs = [obs for obs in observations if obs.external_entity_id == mapping.external_entity_id]
                    all_observations_by_market[mapping.kalshi_market_ticker].extend(entity_obs)

            await self._compute_features(session, all_observations_by_market)
            await session.commit()
            await self._record_health(session, "healthy")
            await session.commit()

        await self.redis.set(
            "external-enrichment:last-run",
            json.dumps({"ran_at": datetime.now(timezone.utc).isoformat(), "providers": provider_counts}),
            ex=self.settings.scheduler_interval_seconds * 2,
        )
        return {"providers": provider_counts, "status": "ok"}

    async def _upsert_sources(self, session: AsyncSession) -> dict[str, ExternalSourceRecord]:
        rows: dict[str, ExternalSourceRecord] = {}
        for provider in self.providers:
            source = provider.source
            health = await provider.healthcheck()
            row = (
                await session.execute(select(ExternalSourceRecord).where(ExternalSourceRecord.slug == source.slug))
            ).scalar_one_or_none()
            if row is None:
                row = ExternalSourceRecord(
                    slug=source.slug,
                    category=source.category.value,
                    display_name=source.display_name,
                    base_url=source.base_url,
                    status=str(health.get("status", "configured")),
                    metadata_json={**source.metadata, "healthcheck": health},
                )
                session.add(row)
                await session.flush()
            else:
                row.category = source.category.value
                row.display_name = source.display_name
                row.base_url = source.base_url
                row.status = str(health.get("status", row.status))
                row.metadata_json = {**source.metadata, "healthcheck": health}
            rows[source.slug] = row
        return rows

    async def _upsert_entities(
        self,
        session: AsyncSession,
        source_id: str,
        entities: list[ExternalEntityModel],
    ) -> dict[str, ExternalEntityRecord]:
        rows: dict[str, ExternalEntityRecord] = {}
        for entity in entities:
            row = (
                await session.execute(
                    select(ExternalEntityRecord).where(
                        ExternalEntityRecord.source_id == source_id,
                        ExternalEntityRecord.external_id == entity.external_id,
                    )
                )
            ).scalar_one_or_none()
            if row is None:
                row = ExternalEntityRecord(
                    source_id=source_id,
                    external_id=entity.external_id,
                    entity_type=entity.entity_type.value,
                    title=entity.title,
                    description=entity.description,
                    resolution_criteria=entity.resolution_criteria,
                    current_probability=entity.current_probability,
                    forecast_value=entity.forecast_value,
                    url=entity.url,
                    category=entity.category,
                    tags=entity.tags,
                    metadata_json=entity.metadata,
                    raw_payload=entity.raw_payload,
                    updated_at=entity.updated_at,
                )
                session.add(row)
                await session.flush()
            else:
                row.entity_type = entity.entity_type.value
                row.title = entity.title
                row.description = entity.description
                row.resolution_criteria = entity.resolution_criteria
                row.current_probability = entity.current_probability
                row.forecast_value = entity.forecast_value
                row.url = entity.url
                row.category = entity.category
                row.tags = entity.tags
                row.metadata_json = entity.metadata
                row.raw_payload = entity.raw_payload
                row.updated_at = entity.updated_at
            rows[entity.external_id] = row
        return rows

    async def _replace_observations(
        self,
        session: AsyncSession,
        source_id: str,
        entity_rows: dict[str, ExternalEntityRecord],
        observations: list[ExternalObservationModel],
    ) -> None:
        external_ids = list(entity_rows.keys())
        if external_ids:
            await session.execute(
                delete(ExternalObservationRecord).where(
                    ExternalObservationRecord.source_id == source_id,
                    ExternalObservationRecord.external_entity_id.in_(external_ids),
                )
            )
        for observation in observations:
            entity_row = entity_rows[observation.external_entity_id]
            session.add(
                ExternalObservationRecord(
                    source_id=source_id,
                    external_entity_id=entity_row.external_id,
                    external_entity_row_id=entity_row.id,
                    observation_type=observation.observation_type.value,
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
            )

    async def _refresh_mappings(
        self,
        session: AsyncSession,
        entities: list[ExternalEntityModel],
        entity_rows: dict[str, ExternalEntityRecord],
        kalshi_markets: list[KalshiMarket],
        overrides: list[ExternalMarketMappingRecord],
    ) -> list[ExternalMarketMappingRecord]:
        created: list[ExternalMarketMappingRecord] = []
        for entity in entities:
            row = entity_rows[entity.external_id]
            mapping = self.mapping_engine.map_entity(entity, kalshi_markets, overrides)
            if mapping is None:
                continue
            existing = (
                await session.execute(
                    select(ExternalMarketMappingRecord).where(
                        ExternalMarketMappingRecord.external_entity_row_id == row.id,
                        ExternalMarketMappingRecord.kalshi_market_ticker == mapping.kalshi_market_ticker,
                    )
                )
            ).scalar_one_or_none()
            if existing is None:
                existing = ExternalMarketMappingRecord(
                    external_entity_id=entity.external_id,
                    external_entity_row_id=row.id,
                    kalshi_market_ticker=mapping.kalshi_market_ticker,
                    confidence_score=mapping.confidence_score,
                    strategy=mapping.strategy,
                    source_notes=mapping.source_notes,
                    manual_override=mapping.manual_override,
                    mismatch_reasons=mapping.mismatch_reasons,
                    ambiguity_score=mapping.ambiguity_score,
                    feature_snapshot=mapping.feature_snapshot,
                    is_active=True,
                )
                session.add(existing)
                await session.flush()
            else:
                existing.confidence_score = mapping.confidence_score
                existing.strategy = mapping.strategy
                existing.source_notes = mapping.source_notes
                existing.manual_override = mapping.manual_override
                existing.mismatch_reasons = mapping.mismatch_reasons
                existing.ambiguity_score = mapping.ambiguity_score
                existing.is_active = True
            created.append(existing)
        return created

    async def _compute_features(
        self,
        session: AsyncSession,
        grouped_observations: dict[str, list[ExternalObservationModel]],
    ) -> None:
        for market_ticker, observations in grouped_observations.items():
            market = await session.get(KalshiMarket, market_ticker)
            if market is None:
                continue
            kalshi_probability = ((market.last_price or market.yes_bid or market.yes_ask or 50) / 100.0)
            feature = build_consensus_feature(
                kalshi_market_ticker=market_ticker,
                kalshi_probability=kalshi_probability,
                observations=observations,
            )
            catalysts = build_catalyst_candidates(observations)
            mappings = list(
                (
                    await session.execute(
                        select(ExternalMarketMappingRecord).where(
                            ExternalMarketMappingRecord.kalshi_market_ticker == market_ticker,
                            ExternalMarketMappingRecord.is_active.is_(True),
                        )
                    )
                ).scalars().all()
            )
            for mapping in mappings:
                mapping.feature_snapshot = {
                    **feature.model_dump(mode="json"),
                    "catalysts": [item.model_dump(mode="json") for item in catalysts],
                }

    async def _record_health(self, session: AsyncSession, status: str) -> None:
        session.add(
            ServiceHealthEvent(
                service_name=self.settings.service_name,
                status=status,
                detail=None,
                payload={},
            )
        )
