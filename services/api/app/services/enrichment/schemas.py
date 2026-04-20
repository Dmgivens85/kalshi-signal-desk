from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum

from pydantic import BaseModel, Field


class EnrichmentProvider(StrEnum):
    SPORTSBOOK = "sportsbook"
    POLYMARKET = "polymarket"
    METACULUS = "metaculus"
    MANIFOLD = "manifold"
    NEWS = "news"


class EnrichmentCategory(StrEnum):
    ODDS = "odds"
    FORECAST = "forecast"
    ARTICLE = "article"


class NormalizedEnrichment(BaseModel):
    provider: EnrichmentProvider
    provider_record_id: str
    category: EnrichmentCategory
    title: str
    summary: str | None = None
    market_ref: str | None = None
    event_ref: str | None = None
    url: str | None = None
    implied_probability: float | None = Field(default=None, ge=0.0, le=1.0)
    source_confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    published_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    tags: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    raw_payload: dict[str, object] = Field(default_factory=dict)


class EnrichmentMapping(BaseModel):
    enrichment_id: str
    market_ticker: str
    confidence: float = Field(ge=0.0, le=1.0)
    strategy: str
    explanation: str
    manual_override: bool = False


class MappingOverride(BaseModel):
    provider: EnrichmentProvider
    provider_record_id: str | None = None
    market_ref: str | None = None
    target_market_ticker: str
    note: str | None = None
    confidence_boost: float = Field(default=0.2, ge=0.0, le=1.0)

