from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class KalshiFeatureSet(BaseModel):
    short_term_momentum: float = 0.0
    move_size: float = 0.0
    spread_width: float = 0.0
    liquidity_depth_score: float = 0.0
    orderbook_imbalance: float = 0.0
    volatility_proxy: float = 0.0
    time_to_resolution_factor: float = 0.0
    unusual_activity_score: float = 0.0


class EnrichmentFeatureSet(BaseModel):
    external_support_score: float = 0.0
    consensus_delta: float = 0.0
    disagreement_score: float = 0.0
    source_count: int = 0
    recency_score: float = 0.0
    catalyst_presence: bool = False
    catalysts: list[dict[str, Any]] = Field(default_factory=list)


class UnifiedSignalInput(BaseModel):
    market_ticker: str
    market_title: str
    market_price: float
    close_time: datetime | None = None
    kalshi_features: KalshiFeatureSet
    enrichment_features: EnrichmentFeatureSet
    risk_context: dict[str, Any] = Field(default_factory=dict)
    open_position_context: dict[str, Any] = Field(default_factory=dict)
    evidence_refs: list[dict[str, Any]] = Field(default_factory=list)


class ComponentScores(BaseModel):
    kalshi_support_score: float
    external_support_score: float
    catalyst_score: float
    confidence_score: float
    risk_penalty_score: float
    overnight_priority_score: float


class ExplainabilityPayload(BaseModel):
    summary: str
    top_supporting_factors: list[str]
    top_weakening_factors: list[str]
    source_count: int
    confidence_score: float
    urgency_tier: str
    suggested_action: str
    suggested_size_bucket: str
    evidence_references: list[dict[str, Any]]


class NotificationCandidate(BaseModel):
    title: str
    message: str
    deep_link: str
    urgency: str
    dedupe_key: str
    expiration_time: datetime | None = None
    overnight_flag: bool = False


class SignalOutput(BaseModel):
    signal_id: str
    market_ticker: str
    direction: str
    confidence_score: float
    kalshi_support_score: float
    external_support_score: float
    risk_penalty_score: float
    urgency_tier: str
    suggested_action: str
    suggested_position_size_bucket: str
    reason_summary: str
    evidence_refs: list[dict[str, Any]]
    created_at: datetime
    expires_at: datetime | None
    overnight_flag: bool
    overnight_priority_score: float
    alert_classification: str
    explainability: ExplainabilityPayload
    notification_candidate: NotificationCandidate | None = None
