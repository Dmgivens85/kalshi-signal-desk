from __future__ import annotations

from collections.abc import Sequence

import httpx

from kalshi_signal_shared import (
    ExternalEntityModel,
    ExternalObservationModel,
    ExternalSourceCategory,
    ExternalSourceModel,
)

from external_enrichment.config import ExternalEnrichmentSettings
from external_enrichment.normalizers.news import build_article_entity, build_article_observation
from .base import ExternalProviderAdapter


class NewsProviderAdapter(ExternalProviderAdapter):
    def __init__(self, settings: ExternalEnrichmentSettings) -> None:
        self.settings = settings
        self.source = ExternalSourceModel(
            slug="news-primary",
            category=ExternalSourceCategory.NEWS,
            display_name="News Primary",
            base_url=settings.news_api_url,
        )

    async def fetch_entities(self) -> list[ExternalEntityModel]:
        items: list[dict[str, object]]
        if self.settings.news_api_url:
            headers = {"Authorization": f"Bearer {self.settings.news_api_key}"} if self.settings.news_api_key else {}
            async with httpx.AsyncClient(timeout=self.settings.request_timeout_seconds) as client:
                response = await client.get(self.settings.news_api_url, headers=headers)
                response.raise_for_status()
                payload = response.json()
                items = payload if isinstance(payload, list) else payload.get("articles", [])
        else:
            items = [
                {
                    "id": "news-fed-revisions",
                    "title": "Labor revisions shift expectations for a June Fed move",
                    "summary": "Macro desks and economists adjusted rate path expectations after revisions.",
                    "url": "https://example.com/news/fed-revisions",
                    "tags": ["fed", "macro"],
                    "entities": ["FED-2026-CUTS", "FOMC"],
                    "raw_text_available": False,
                }
            ]
        return [
            build_article_entity(
                source_slug=self.source.slug,
                article_id=str(item["id"]),
                title=str(item["title"]),
                summary=item.get("summary"),
                url=item.get("url"),
                tags=item.get("tags", []),
                raw_payload=item,
            )
            for item in items
        ]

    async def fetch_markets_or_questions(self) -> list[ExternalEntityModel]:
        return await self.fetch_entities()

    async def fetch_observations(self, entities: Sequence[ExternalEntityModel]) -> list[ExternalObservationModel]:
        observations: list[ExternalObservationModel] = []
        for entity in entities:
            raw = entity.raw_payload
            observations.append(
                build_article_observation(
                    source_slug=self.source.slug,
                    article_id=entity.external_id,
                    title=entity.title,
                    summary=entity.description,
                    url=entity.url,
                    tags=entity.tags,
                    entities=list(raw.get("entities", [])),
                    raw_text_available=bool(raw.get("raw_text_available", False)),
                    raw_payload=raw,
                )
            )
        return observations

    async def normalize(
        self,
        entities: Sequence[ExternalEntityModel],
        observations: Sequence[ExternalObservationModel],
    ) -> tuple[list[ExternalEntityModel], list[ExternalObservationModel]]:
        return list(entities), list(observations)

    async def healthcheck(self) -> dict[str, object]:
        return {"source": self.source.slug, "status": "healthy", "base_url": self.settings.news_api_url}
