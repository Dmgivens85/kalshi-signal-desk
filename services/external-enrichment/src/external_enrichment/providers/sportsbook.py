from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timedelta, timezone

import httpx

from kalshi_signal_shared import (
    ExternalEntityModel,
    ExternalEntityType,
    ExternalObservationModel,
    ExternalObservationType,
    ExternalSourceCategory,
    ExternalSourceModel,
)

from external_enrichment.config import ExternalEnrichmentSettings
from external_enrichment.normalizers.sportsbook import american_odds_to_probability
from .base import ExternalProviderAdapter


def _recent(minutes: int) -> datetime:
    return datetime.now(timezone.utc) - timedelta(minutes=minutes)


class _SportsbookBaseAdapter(ExternalProviderAdapter):
    def __init__(self, settings: ExternalEnrichmentSettings, *, slug: str, display_name: str, base_url: str | None) -> None:
        self.settings = settings
        self.base_url = base_url
        self.source = ExternalSourceModel(
            slug=slug,
            category=ExternalSourceCategory.SPORTSBOOK,
            display_name=display_name,
            base_url=base_url,
        )

    async def fetch_entities(self) -> list[ExternalEntityModel]:
        if self.base_url:
            async with httpx.AsyncClient(timeout=self.settings.request_timeout_seconds) as client:
                response = await client.get(self.base_url)
                response.raise_for_status()
                payload = response.json()
                items = payload if isinstance(payload, list) else payload.get("items", [])
        else:
            items = [
                {
                    "id": f"{self.source.slug}-fed-cuts",
                    "title": "Fed cut by June 2026",
                    "description": "Consensus pricing for a June 2026 rate cut.",
                    "probability": 0.66,
                    "market_ref": "FED-2026-CUTS",
                },
                {
                    "id": f"{self.source.slug}-house",
                    "title": "Democrats win the House in 2026",
                    "description": "Election market leaning on district quality and fundraising.",
                    "probability": 0.58,
                    "market_ref": "ELECTION-HOUSE-2026",
                },
            ]

        entities: list[ExternalEntityModel] = []
        for item in items:
            probability = item.get("probability")
            odds = item.get("american_odds")
            if probability is None and odds is not None:
                probability = american_odds_to_probability(odds)
            entities.append(
                ExternalEntityModel(
                    source_slug=self.source.slug,
                    external_id=str(item.get("id")),
                    entity_type=ExternalEntityType.MARKET,
                    title=item.get("title", "Sportsbook market"),
                    description=item.get("description"),
                    current_probability=probability,
                    url=item.get("url"),
                    category=item.get("category", "sportsbook"),
                    tags=item.get("tags", ["odds", "consensus"]),
                    metadata={"market_ref": item.get("market_ref")},
                    raw_payload=item,
                    updated_at=_recent(10),
                )
            )
        return entities

    async def fetch_markets_or_questions(self) -> list[ExternalEntityModel]:
        return await self.fetch_entities()

    async def fetch_observations(self, entities: Sequence[ExternalEntityModel]) -> list[ExternalObservationModel]:
        return [
            ExternalObservationModel(
                source_slug=self.source.slug,
                external_entity_id=entity.external_id,
                observation_type=ExternalObservationType.PRICE_SNAPSHOT,
                observed_at=_recent(10),
                probability_value=entity.current_probability,
                title=entity.title,
                summary=entity.description,
                url=entity.url,
                tags=entity.tags,
                ai_metadata={"market_ref": entity.metadata.get("market_ref")},
                raw_payload=entity.raw_payload,
            )
            for entity in entities
        ]

    async def normalize(
        self,
        entities: Sequence[ExternalEntityModel],
        observations: Sequence[ExternalObservationModel],
    ) -> tuple[list[ExternalEntityModel], list[ExternalObservationModel]]:
        return list(entities), list(observations)

    async def healthcheck(self) -> dict[str, object]:
        return {"source": self.source.slug, "status": "healthy", "base_url": self.base_url}


class SportsbookPrimaryAdapter(_SportsbookBaseAdapter):
    def __init__(self, settings: ExternalEnrichmentSettings) -> None:
        super().__init__(settings, slug="sportsbook-primary", display_name="Sportsbook Primary", base_url=settings.sportsbook_primary_url)


class SportsbookSecondaryAdapter(_SportsbookBaseAdapter):
    def __init__(self, settings: ExternalEnrichmentSettings) -> None:
        super().__init__(settings, slug="sportsbook-secondary", display_name="Sportsbook Secondary", base_url=settings.sportsbook_secondary_url)
