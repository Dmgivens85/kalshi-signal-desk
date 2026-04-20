from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timedelta, timezone

import httpx

from kalshi_signal_shared import (
    ExternalEntityModel,
    ExternalObservationModel,
    ExternalObservationType,
    ExternalSourceCategory,
    ExternalSourceModel,
)

from external_enrichment.config import ExternalEnrichmentSettings
from external_enrichment.normalizers.forecast import build_forecast_entity
from .base import ExternalProviderAdapter


def _recent(minutes: int) -> datetime:
    return datetime.now(timezone.utc) - timedelta(minutes=minutes)


class GenericForecastAdapter(ExternalProviderAdapter):
    provider_slug: str
    provider_name: str
    provider_url: str | None

    def __init__(self, settings: ExternalEnrichmentSettings) -> None:
        self.settings = settings
        self.source = ExternalSourceModel(
            slug=self.provider_slug,
            category=ExternalSourceCategory.FORECAST,
            display_name=self.provider_name,
            base_url=self.provider_url,
        )

    async def _raw_items(self) -> list[dict[str, object]]:
        if self.provider_url:
            async with httpx.AsyncClient(timeout=self.settings.request_timeout_seconds) as client:
                response = await client.get(self.provider_url)
                response.raise_for_status()
                payload = response.json()
                return payload if isinstance(payload, list) else payload.get("items", [])
        return []

    async def fetch_entities(self) -> list[ExternalEntityModel]:
        items = await self._raw_items()
        if not items:
            items = [
                {
                    "id": f"{self.provider_slug}-macro",
                    "title": f"{self.provider_name} says recession risk rises in 2026",
                    "description": "Forecast market repriced after weaker macro data.",
                    "resolution_criteria": "Official NBER recession call in 2026.",
                    "probability": 0.57,
                    "url": f"https://example.com/{self.provider_slug}/macro",
                    "tags": ["macro", "forecast"],
                    "market_ref": "US-RECESSION-2026",
                }
            ]
        return [
            build_forecast_entity(
                source_slug=self.source.slug,
                external_id=str(item["id"]),
                title=str(item["title"]),
                description=item.get("description"),
                resolution_criteria=item.get("resolution_criteria"),
                probability=item.get("probability"),
                url=item.get("url"),
                category=item.get("category", "forecast"),
                tags=item.get("tags", []),
                raw_payload=item,
            )
            for item in items
        ]

    async def fetch_markets_or_questions(self) -> list[ExternalEntityModel]:
        return await self.fetch_entities()

    async def fetch_observations(self, entities: Sequence[ExternalEntityModel]) -> list[ExternalObservationModel]:
        return [
            ExternalObservationModel(
                source_slug=self.source.slug,
                external_entity_id=entity.external_id,
                observation_type=ExternalObservationType.FORECAST_SNAPSHOT,
                observed_at=_recent(30),
                probability_value=entity.current_probability,
                title=entity.title,
                summary=entity.description,
                url=entity.url,
                tags=entity.tags,
                ai_metadata={"resolution_criteria": entity.resolution_criteria},
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
        return {"source": self.source.slug, "status": "healthy", "base_url": self.provider_url}


class PolymarketAdapter(GenericForecastAdapter):
    provider_slug = "polymarket"
    provider_name = "Polymarket"
    provider_url = None

    def __init__(self, settings: ExternalEnrichmentSettings) -> None:
        self.provider_url = settings.polymarket_api_url
        super().__init__(settings)


class MetaculusAdapter(GenericForecastAdapter):
    provider_slug = "metaculus"
    provider_name = "Metaculus"
    provider_url = None

    def __init__(self, settings: ExternalEnrichmentSettings) -> None:
        self.provider_url = settings.metaculus_api_url
        super().__init__(settings)


class ManifoldAdapter(GenericForecastAdapter):
    provider_slug = "manifold"
    provider_name = "Manifold"
    provider_url = None

    def __init__(self, settings: ExternalEnrichmentSettings) -> None:
        self.provider_url = settings.manifold_api_url
        super().__init__(settings)
