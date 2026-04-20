from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone

import httpx

from app.core.config import APISettings
from app.services.enrichment.schemas import EnrichmentCategory, EnrichmentProvider, NormalizedEnrichment


class ExternalProviderAdapter(ABC):
    provider: EnrichmentProvider

    def __init__(self, settings: APISettings) -> None:
        self.settings = settings

    @abstractmethod
    async def fetch(self) -> list[NormalizedEnrichment]:
        raise NotImplementedError


def _fresh_timestamp(minutes_ago: int) -> datetime:
    return datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)


class SportsbookOddsAdapter(ExternalProviderAdapter):
    provider = EnrichmentProvider.SPORTSBOOK

    async def fetch(self) -> list[NormalizedEnrichment]:
        if self.settings.sportsbook_odds_api_url:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(self.settings.sportsbook_odds_api_url)
                response.raise_for_status()
                payload = response.json()
                items = payload if isinstance(payload, list) else payload.get("items", [])
        else:
            items = [
                {
                    "id": "sb-fed-cuts",
                    "title": "Street pricing drifts toward a June rate cut",
                    "market_ref": "FED-2026-CUTS",
                    "probability": 0.69,
                    "summary": "Consensus sportsbook desks moved implied odds higher after softer labor revisions.",
                }
            ]

        return [
            NormalizedEnrichment(
                provider=self.provider,
                provider_record_id=str(item.get("id", item.get("market_ref", "unknown"))),
                category=EnrichmentCategory.ODDS,
                title=item.get("title", "Sportsbook odds"),
                summary=item.get("summary"),
                market_ref=item.get("market_ref"),
                implied_probability=float(item.get("probability", 0.5)),
                source_confidence=0.72,
                published_at=_fresh_timestamp(18),
                evidence=["Sportsbook consensus", "Cross-book pricing"],
                raw_payload=item,
            )
            for item in items
        ]


class PolymarketAdapter(ExternalProviderAdapter):
    provider = EnrichmentProvider.POLYMARKET

    async def fetch(self) -> list[NormalizedEnrichment]:
        items = [
            {
                "id": "poly-recession",
                "title": "Polymarket macro traders lean toward slower growth",
                "market_ref": "US-RECESSION-2026",
                "probability": 0.61,
                "summary": "Open interest picked up after ISM softness and bank tightening commentary.",
            }
        ]
        return [
            NormalizedEnrichment(
                provider=self.provider,
                provider_record_id=item["id"],
                category=EnrichmentCategory.FORECAST,
                title=item["title"],
                summary=item["summary"],
                market_ref=item["market_ref"],
                implied_probability=item["probability"],
                source_confidence=0.68,
                published_at=_fresh_timestamp(24),
                tags=["prediction-market", "cross-venue"],
                evidence=["On-chain volume shift"],
                raw_payload=item,
            )
            for item in items
        ]


class MetaculusAdapter(ExternalProviderAdapter):
    provider = EnrichmentProvider.METACULUS

    async def fetch(self) -> list[NormalizedEnrichment]:
        items = [
            {
                "id": "meta-house",
                "title": "Metaculus community drifts toward tighter House race distribution",
                "market_ref": "ELECTION-HOUSE-2026",
                "probability": 0.64,
                "summary": "Forecasters cite fundraising and district-quality spread rather than top-line polling.",
            }
        ]
        return [
            NormalizedEnrichment(
                provider=self.provider,
                provider_record_id=item["id"],
                category=EnrichmentCategory.FORECAST,
                title=item["title"],
                summary=item["summary"],
                market_ref=item["market_ref"],
                implied_probability=item["probability"],
                source_confidence=0.74,
                published_at=_fresh_timestamp(90),
                tags=["forecast-community"],
                evidence=["Community median"],
                raw_payload=item,
            )
            for item in items
        ]


class ManifoldAdapter(ExternalProviderAdapter):
    provider = EnrichmentProvider.MANIFOLD

    async def fetch(self) -> list[NormalizedEnrichment]:
        items = [
            {
                "id": "mani-fed",
                "title": "Manifold traders repriced soft-landing confidence lower",
                "market_ref": "FED-2026-CUTS",
                "probability": 0.73,
                "summary": "Retail prediction flow aligned with dovish macro narratives in the last session.",
            }
        ]
        return [
            NormalizedEnrichment(
                provider=self.provider,
                provider_record_id=item["id"],
                category=EnrichmentCategory.FORECAST,
                title=item["title"],
                summary=item["summary"],
                market_ref=item["market_ref"],
                implied_probability=item["probability"],
                source_confidence=0.63,
                published_at=_fresh_timestamp(32),
                tags=["retail-flow"],
                evidence=["Retail prediction market"],
                raw_payload=item,
            )
            for item in items
        ]


class NewsAdapter(ExternalProviderAdapter):
    provider = EnrichmentProvider.NEWS

    async def fetch(self) -> list[NormalizedEnrichment]:
        items = [
            {
                "id": "news-labor-revision",
                "title": "Labor revisions raise pressure on Fed path markets",
                "market_ref": "FED-2026-CUTS",
                "summary": "Revisions and softer forward indicators increased the odds of a near-term policy pivot.",
                "url": "https://example.com/labor-revisions-fed-path",
                "confidence": 0.66,
            },
            {
                "id": "news-house-fundraising",
                "title": "District fundraising divergence widens ahead of House cycle",
                "market_ref": "ELECTION-HOUSE-2026",
                "summary": "Competitive seat fundraising spread is outpacing recent polling moves.",
                "url": "https://example.com/house-fundraising-divergence",
                "confidence": 0.61,
            },
        ]
        return [
            NormalizedEnrichment(
                provider=self.provider,
                provider_record_id=item["id"],
                category=EnrichmentCategory.ARTICLE,
                title=item["title"],
                summary=item["summary"],
                market_ref=item["market_ref"],
                url=item["url"],
                implied_probability=None,
                source_confidence=item["confidence"],
                published_at=_fresh_timestamp(70),
                tags=["news"],
                evidence=[item["summary"]],
                raw_payload=item,
            )
            for item in items
        ]


def build_enrichment_adapters(settings: APISettings) -> list[ExternalProviderAdapter]:
    return [
        SportsbookOddsAdapter(settings),
        PolymarketAdapter(settings),
        MetaculusAdapter(settings),
        ManifoldAdapter(settings),
        NewsAdapter(settings),
    ]
