from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import APISettings
from app.db.models import EnrichmentMappingRecord, EnrichmentRecord, MappingOverrideRecord, MarketSnapshot
from app.services.enrichment.adapters import build_enrichment_adapters
from app.services.enrichment.mapping import map_enrichment_to_market


class ExternalEnrichmentService:
    def __init__(self, settings: APISettings, db: AsyncSession) -> None:
        self.settings = settings
        self.db = db

    async def collect_and_store(self) -> dict[str, object]:
        adapters = build_enrichment_adapters(self.settings)
        normalized: list[EnrichmentRecord] = []
        mappings: list[EnrichmentMappingRecord] = []

        result = await self.db.execute(select(MarketSnapshot))
        markets = result.scalars().all()
        overrides_result = await self.db.execute(
            select(MappingOverrideRecord).where(MappingOverrideRecord.is_active.is_(True))
        )
        overrides = overrides_result.scalars().all()

        await self.db.execute(delete(EnrichmentMappingRecord))
        await self.db.execute(delete(EnrichmentRecord))

        for adapter in adapters:
            items = await adapter.fetch()
            for item in items:
                record = EnrichmentRecord(
                    provider=item.provider.value,
                    provider_record_id=item.provider_record_id,
                    category=item.category.value,
                    title=item.title,
                    market_ref=item.market_ref,
                    url=item.url,
                    implied_probability=item.implied_probability,
                    confidence=item.source_confidence,
                    published_at=item.published_at,
                    normalized_payload=item.model_dump(mode="json"),
                    raw_payload=item.raw_payload,
                )
                self.db.add(record)
                await self.db.flush()
                normalized.append(record)

                mapping = map_enrichment_to_market(record.id, item, markets, overrides)
                if mapping is None:
                    continue
                mapping_record = EnrichmentMappingRecord(
                    enrichment_id=record.id,
                    market_ticker=mapping.market_ticker,
                    confidence=mapping.confidence,
                    strategy=mapping.strategy,
                    explanation=mapping.explanation,
                    manual_override=mapping.manual_override,
                )
                self.db.add(mapping_record)
                mappings.append(mapping_record)

        await self.db.commit()
        return {
            "providers": [adapter.provider.value for adapter in adapters],
            "enrichment_count": len(normalized),
            "mapping_count": len(mappings),
        }

    async def list_enrichments(self) -> dict[str, object]:
        enrichments = (await self.db.execute(select(EnrichmentRecord).order_by(EnrichmentRecord.created_at.desc()))).scalars().all()
        mappings = (await self.db.execute(select(EnrichmentMappingRecord))).scalars().all()
        return {
            "enrichments": [item.to_dict() for item in enrichments],
            "mappings": [item.to_dict() for item in mappings],
        }
