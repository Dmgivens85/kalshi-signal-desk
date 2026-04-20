from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ExternalSourceCategory(StrEnum):
    SPORTSBOOK = "sportsbook"
    FORECAST = "forecast"
    NEWS = "news"


class ExternalEntityType(StrEnum):
    MARKET = "market"
    QUESTION = "question"
    ARTICLE = "article"
    EVENT = "event"


class ExternalObservationType(StrEnum):
    PRICE_SNAPSHOT = "price_snapshot"
    FORECAST_SNAPSHOT = "forecast_snapshot"
    NEWS_ARTICLE = "news_article"
    FEATURE_SNAPSHOT = "feature_snapshot"


class ExternalSourceModel(BaseModel):
    slug: str
    category: ExternalSourceCategory
    display_name: str
    base_url: str | None = None
    status: str = "configured"
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExternalEntityModel(BaseModel):
    source_slug: str
    external_id: str
    entity_type: ExternalEntityType
    title: str
    description: str | None = None
    resolution_criteria: str | None = None
    current_probability: float | None = Field(default=None, ge=0.0, le=1.0)
    forecast_value: float | None = None
    url: str | None = None
    category: str | None = None
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    raw_payload: dict[str, Any] = Field(default_factory=dict)
    updated_at: datetime = Field(default_factory=utcnow)


class ExternalObservationModel(BaseModel):
    source_slug: str
    external_entity_id: str
    observation_type: ExternalObservationType
    observed_at: datetime = Field(default_factory=utcnow)
    probability_value: float | None = Field(default=None, ge=0.0, le=1.0)
    numeric_value: float | None = None
    title: str | None = None
    summary: str | None = None
    url: str | None = None
    tags: list[str] = Field(default_factory=list)
    entities: list[str] = Field(default_factory=list)
    raw_text_available: bool = False
    ai_metadata: dict[str, Any] = Field(default_factory=dict)
    raw_payload: dict[str, Any] = Field(default_factory=dict)


class ExternalMappingModel(BaseModel):
    external_entity_id: str
    kalshi_market_ticker: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    strategy: str
    source_notes: str
    manual_override: bool = False
    mismatch_reasons: list[str] = Field(default_factory=list)
    ambiguity_score: float = Field(default=0.0, ge=0.0, le=1.0)
    feature_snapshot: dict[str, Any] = Field(default_factory=dict)


class ExternalConsensusFeature(BaseModel):
    kalshi_market_ticker: str
    external_support_score: float = Field(ge=0.0, le=1.0)
    consensus_delta: float
    disagreement_score: float = Field(ge=0.0, le=1.0)
    source_count: int = Field(ge=0)
    recency_score: float = Field(ge=0.0, le=1.0)
    catalyst_presence: bool
    feature_details: dict[str, Any] = Field(default_factory=dict)


class NewsCatalystCandidate(BaseModel):
    external_entity_id: str
    article_id: str
    title: str
    summary: str | None = None
    published_at: datetime = Field(default_factory=utcnow)
    url: str | None = None
    tags: list[str] = Field(default_factory=list)
    entities: list[str] = Field(default_factory=list)
    relevance_hints: list[str] = Field(default_factory=list)
