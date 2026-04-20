from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    email: Mapped[str] = mapped_column(String(320), unique=True)
    display_name: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(64), default="analyst")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "email": self.email,
            "display_name": self.display_name,
            "role": self.role,
            "is_active": self.is_active,
        }


class KalshiCredential(Base, TimestampMixin):
    __tablename__ = "kalshi_credentials"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    key_id: Mapped[str] = mapped_column(String(255))
    environment: Mapped[str] = mapped_column(String(32))
    private_key_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    last_validated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class KalshiMarket(Base, TimestampMixin):
    __tablename__ = "kalshi_markets"

    ticker: Mapped[str] = mapped_column(String(128), primary_key=True)
    event_ticker: Mapped[str] = mapped_column(String(128), index=True)
    series_ticker: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(512))
    subtitle: Mapped[str | None] = mapped_column(String(512), nullable=True)
    market_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    close_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_price: Mapped[int | None] = mapped_column(Integer, nullable=True)
    yes_bid: Mapped[int | None] = mapped_column(Integer, nullable=True)
    yes_ask: Mapped[int | None] = mapped_column(Integer, nullable=True)
    volume: Mapped[int | None] = mapped_column(Integer, nullable=True)
    open_interest: Mapped[int | None] = mapped_column(Integer, nullable=True)
    liquidity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_observed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ticker": self.ticker,
            "event_ticker": self.event_ticker,
            "series_ticker": self.series_ticker,
            "title": self.title,
            "subtitle": self.subtitle,
            "market_type": self.market_type,
            "status": self.status,
            "close_time": self.close_time.isoformat() if self.close_time else None,
            "last_price": self.last_price,
            "yes_bid": self.yes_bid,
            "yes_ask": self.yes_ask,
            "volume": self.volume,
            "open_interest": self.open_interest,
            "liquidity": self.liquidity,
            "last_observed_at": self.last_observed_at.isoformat() if self.last_observed_at else None,
        }


class MarketSnapshot(Base, TimestampMixin):
    __tablename__ = "market_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    market_ticker: Mapped[str] = mapped_column(String(128), ForeignKey("kalshi_markets.ticker", ondelete="CASCADE"), index=True)
    event_ticker: Mapped[str] = mapped_column(String(128), index=True)
    title: Mapped[str] = mapped_column(String(512))
    status: Mapped[str] = mapped_column(String(32))
    close_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_price: Mapped[int | None] = mapped_column(Integer, nullable=True)
    yes_bid: Mapped[int | None] = mapped_column(Integer, nullable=True)
    yes_ask: Mapped[int | None] = mapped_column(Integer, nullable=True)
    volume: Mapped[int | None] = mapped_column(Integer, nullable=True)
    open_interest: Mapped[int | None] = mapped_column(Integer, nullable=True)
    liquidity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    snapshot_type: Mapped[str] = mapped_column(String(32), default="ticker")
    sequence_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    bid_levels: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    ask_levels: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    @classmethod
    def from_market_payload(
        cls,
        payload: dict[str, Any],
        *,
        raw_payload: dict[str, Any] | None = None,
    ) -> "MarketSnapshot":
        return cls(
            market_ticker=payload.get("ticker") or payload.get("market_ticker"),
            event_ticker=payload.get("event_ticker", ""),
            title=payload["title"],
            status=payload.get("status", "unknown"),
            close_time=payload.get("close_time"),
            last_price=payload.get("last_price"),
            yes_bid=payload.get("yes_bid"),
            yes_ask=payload.get("yes_ask"),
            volume=payload.get("volume"),
            open_interest=payload.get("open_interest"),
            liquidity=payload.get("liquidity"),
            snapshot_type=payload.get("snapshot_type", "ticker"),
            sequence_number=payload.get("sequence_number"),
            observed_at=payload.get("observed_at", utcnow()),
            bid_levels=payload.get("bid_levels", []),
            ask_levels=payload.get("ask_levels", []),
            raw_payload=raw_payload or payload,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "market_ticker": self.market_ticker,
            "event_ticker": self.event_ticker,
            "title": self.title,
            "status": self.status,
            "close_time": self.close_time.isoformat() if self.close_time else None,
            "last_price": self.last_price,
            "yes_bid": self.yes_bid,
            "yes_ask": self.yes_ask,
            "volume": self.volume,
            "open_interest": self.open_interest,
            "liquidity": self.liquidity,
            "snapshot_type": self.snapshot_type,
            "sequence_number": self.sequence_number,
            "observed_at": self.observed_at.isoformat(),
            "bid_levels": self.bid_levels,
            "ask_levels": self.ask_levels,
        }


class OrderbookEvent(Base, TimestampMixin):
    __tablename__ = "orderbook_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    market_ticker: Mapped[str] = mapped_column(String(128), ForeignKey("kalshi_markets.ticker", ondelete="CASCADE"), index=True)
    event_type: Mapped[str] = mapped_column(String(32), index=True)
    sequence_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    side: Mapped[str | None] = mapped_column(String(8), nullable=True)
    price: Mapped[int | None] = mapped_column(Integer, nullable=True)
    delta: Mapped[int | None] = mapped_column(Integer, nullable=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    bid_levels: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    ask_levels: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class ServiceHealthEvent(Base):
    __tablename__ = "service_health_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    service_name: Mapped[str] = mapped_column(String(128), index=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class SignalRecord(Base, TimestampMixin):
    __tablename__ = "signals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    market_ticker: Mapped[str] = mapped_column(String(128), index=True)
    signal_type: Mapped[str] = mapped_column(String(64))
    thesis: Mapped[str] = mapped_column(Text)
    confidence: Mapped[float] = mapped_column(Float)
    horizon: Mapped[str] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(32), default="active")
    market_title: Mapped[str | None] = mapped_column(String(512), nullable=True)
    recommended_action: Mapped[str | None] = mapped_column(String(64), nullable=True)
    reason_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_count: Mapped[int] = mapped_column(Integer, default=0)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    feature_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_by_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    strategy_id: Mapped[str | None] = mapped_column(ForeignKey("strategies.id"), nullable=True)
    direction: Mapped[str | None] = mapped_column(String(16), nullable=True)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    kalshi_support_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    external_support_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    risk_penalty_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    overnight_priority_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    urgency_tier: Mapped[str | None] = mapped_column(String(32), nullable=True)
    suggested_position_size_bucket: Mapped[str | None] = mapped_column(String(32), nullable=True)
    evidence_refs: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    overnight_flag: Mapped[bool] = mapped_column(Boolean, default=False)
    dedupe_key: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    alert_classification: Mapped[str | None] = mapped_column(String(64), nullable=True)
    notification_candidate_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "market_ticker": self.market_ticker,
            "market_title": self.market_title,
            "signal_type": self.signal_type,
            "thesis": self.thesis,
            "confidence": self.confidence,
            "horizon": self.horizon,
            "status": self.status,
            "recommended_action": self.recommended_action,
            "reason_summary": self.reason_summary,
            "source_count": self.source_count,
            "metadata_json": self.metadata_json,
            "feature_payload": self.feature_payload,
            "direction": self.direction,
            "confidence_score": self.confidence_score if self.confidence_score is not None else self.confidence,
            "kalshi_support_score": self.kalshi_support_score,
            "external_support_score": self.external_support_score,
            "risk_penalty_score": self.risk_penalty_score,
            "overnight_priority_score": self.overnight_priority_score,
            "urgency_tier": self.urgency_tier,
            "suggested_action": self.recommended_action,
            "suggested_position_size_bucket": self.suggested_position_size_bucket,
            "evidence_refs": self.evidence_refs,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "overnight_flag": self.overnight_flag,
            "dedupe_key": self.dedupe_key,
            "alert_classification": self.alert_classification,
            "notification_candidate_payload": self.notification_candidate_payload,
            "created_at": self.created_at.isoformat(),
        }


class StrategyRecord(Base, TimestampMixin):
    __tablename__ = "strategies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    config_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "slug": self.slug,
            "name": self.name,
            "description": self.description,
            "is_active": self.is_active,
            "config_json": self.config_json,
        }


class SignalFeatureRecord(Base, TimestampMixin):
    __tablename__ = "signal_features"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    signal_id: Mapped[str] = mapped_column(ForeignKey("signals.id", ondelete="CASCADE"), index=True)
    feature_group: Mapped[str] = mapped_column(String(64), index=True)
    feature_name: Mapped[str] = mapped_column(String(128), index=True)
    feature_value: Mapped[float] = mapped_column(Float)
    feature_unit: Mapped[str | None] = mapped_column(String(32), nullable=True)
    is_supporting: Mapped[bool] = mapped_column(Boolean, default=True)
    detail_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "signal_id": self.signal_id,
            "feature_group": self.feature_group,
            "feature_name": self.feature_name,
            "feature_value": self.feature_value,
            "feature_unit": self.feature_unit,
            "is_supporting": self.is_supporting,
            "detail_json": self.detail_json,
        }


class AlertEventRecord(Base, TimestampMixin):
    __tablename__ = "alert_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    signal_id: Mapped[str | None] = mapped_column(ForeignKey("signals.id", ondelete="SET NULL"), nullable=True, index=True)
    market_ticker: Mapped[str] = mapped_column(String(128), index=True)
    dedupe_key: Mapped[str] = mapped_column(String(255), index=True)
    alert_type: Mapped[str] = mapped_column(String(64), index=True)
    urgency: Mapped[str] = mapped_column(String(32), index=True)
    overnight_flag: Mapped[bool] = mapped_column(Boolean, default=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delivery_status: Mapped[str] = mapped_column(String(32), default="candidate")
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "signal_id": self.signal_id,
            "market_ticker": self.market_ticker,
            "dedupe_key": self.dedupe_key,
            "alert_type": self.alert_type,
            "urgency": self.urgency,
            "overnight_flag": self.overnight_flag,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "delivery_status": self.delivery_status,
            "payload": self.payload,
        }


class EnrichmentRecord(Base, TimestampMixin):
    __tablename__ = "enrichments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    provider: Mapped[str] = mapped_column(String(64), index=True)
    provider_record_id: Mapped[str] = mapped_column(String(255), index=True)
    category: Mapped[str] = mapped_column(String(64))
    title: Mapped[str] = mapped_column(String(512))
    market_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    implied_probability: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    normalized_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "provider": self.provider,
            "provider_record_id": self.provider_record_id,
            "category": self.category,
            "title": self.title,
            "market_ref": self.market_ref,
            "url": self.url,
            "implied_probability": self.implied_probability,
            "confidence": self.confidence,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "normalized_payload": self.normalized_payload,
        }


class EnrichmentMappingRecord(Base, TimestampMixin):
    __tablename__ = "enrichment_mappings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    enrichment_id: Mapped[str] = mapped_column(ForeignKey("enrichments.id", ondelete="CASCADE"), index=True)
    market_ticker: Mapped[str] = mapped_column(String(128), index=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    strategy: Mapped[str] = mapped_column(String(64))
    explanation: Mapped[str] = mapped_column(Text)
    manual_override: Mapped[bool] = mapped_column(Boolean, default=False)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "enrichment_id": self.enrichment_id,
            "market_ticker": self.market_ticker,
            "confidence": self.confidence,
            "strategy": self.strategy,
            "explanation": self.explanation,
            "manual_override": self.manual_override,
        }


class MappingOverrideRecord(Base, TimestampMixin):
    __tablename__ = "mapping_overrides"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    provider: Mapped[str] = mapped_column(String(64), index=True)
    provider_record_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    market_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    target_market_ticker: Mapped[str] = mapped_column(String(128), index=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence_boost: Mapped[float] = mapped_column(Float, default=0.2)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "provider": self.provider,
            "provider_record_id": self.provider_record_id,
            "market_ref": self.market_ref,
            "target_market_ticker": self.target_market_ticker,
            "note": self.note,
            "confidence_boost": self.confidence_boost,
            "is_active": self.is_active,
        }


class ExternalSourceRecord(Base, TimestampMixin):
    __tablename__ = "external_sources"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    category: Mapped[str] = mapped_column(String(32), index=True)
    display_name: Mapped[str] = mapped_column(String(255))
    base_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="configured")
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "slug": self.slug,
            "category": self.category,
            "display_name": self.display_name,
            "base_url": self.base_url,
            "status": self.status,
            "metadata_json": self.metadata_json,
            "last_synced_at": self.last_synced_at.isoformat() if self.last_synced_at else None,
            "last_error": self.last_error,
        }


class ExternalEntityRecord(Base, TimestampMixin):
    __tablename__ = "external_entities"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    source_id: Mapped[str] = mapped_column(ForeignKey("external_sources.id", ondelete="CASCADE"), index=True)
    external_id: Mapped[str] = mapped_column(String(255), index=True)
    entity_type: Mapped[str] = mapped_column(String(32), index=True)
    title: Mapped[str] = mapped_column(String(512))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolution_criteria: Mapped[str | None] = mapped_column(Text, nullable=True)
    current_probability: Mapped[float | None] = mapped_column(Float, nullable=True)
    forecast_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    category: Mapped[str | None] = mapped_column(String(128), nullable=True)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "source_id": self.source_id,
            "external_id": self.external_id,
            "entity_type": self.entity_type,
            "title": self.title,
            "description": self.description,
            "resolution_criteria": self.resolution_criteria,
            "current_probability": self.current_probability,
            "forecast_value": self.forecast_value,
            "url": self.url,
            "category": self.category,
            "tags": self.tags,
            "metadata_json": self.metadata_json,
        }


class ExternalObservationRecord(Base, TimestampMixin):
    __tablename__ = "external_observations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    source_id: Mapped[str] = mapped_column(ForeignKey("external_sources.id", ondelete="CASCADE"), index=True)
    external_entity_row_id: Mapped[str] = mapped_column(
        ForeignKey("external_entities.id", ondelete="CASCADE"),
        index=True,
    )
    external_entity_id: Mapped[str] = mapped_column(String(255), index=True)
    observation_type: Mapped[str] = mapped_column(String(32), index=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    probability_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    numeric_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    title: Mapped[str | None] = mapped_column(String(512), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    entities: Mapped[list[str]] = mapped_column(JSON, default=list)
    raw_text_available: Mapped[bool] = mapped_column(Boolean, default=False)
    ai_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "source_id": self.source_id,
            "external_entity_row_id": self.external_entity_row_id,
            "external_entity_id": self.external_entity_id,
            "observation_type": self.observation_type,
            "observed_at": self.observed_at.isoformat(),
            "probability_value": self.probability_value,
            "numeric_value": self.numeric_value,
            "title": self.title,
            "summary": self.summary,
            "url": self.url,
            "tags": self.tags,
            "entities": self.entities,
            "raw_text_available": self.raw_text_available,
            "ai_metadata": self.ai_metadata,
        }


class ExternalMarketMappingRecord(Base, TimestampMixin):
    __tablename__ = "external_market_mappings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    external_entity_row_id: Mapped[str] = mapped_column(
        ForeignKey("external_entities.id", ondelete="CASCADE"),
        index=True,
    )
    external_entity_id: Mapped[str] = mapped_column(String(255), index=True)
    kalshi_market_ticker: Mapped[str] = mapped_column(
        String(128),
        ForeignKey("kalshi_markets.ticker", ondelete="CASCADE"),
        index=True,
    )
    confidence_score: Mapped[float] = mapped_column(Float, default=0.5)
    strategy: Mapped[str] = mapped_column(String(64))
    source_notes: Mapped[str] = mapped_column(Text)
    manual_override: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    mismatch_reasons: Mapped[list[str]] = mapped_column(JSON, default=list)
    ambiguity_score: Mapped[float] = mapped_column(Float, default=0.0)
    feature_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "external_entity_row_id": self.external_entity_row_id,
            "external_entity_id": self.external_entity_id,
            "kalshi_market_ticker": self.kalshi_market_ticker,
            "confidence_score": self.confidence_score,
            "strategy": self.strategy,
            "source_notes": self.source_notes,
            "manual_override": self.manual_override,
            "is_active": self.is_active,
            "mismatch_reasons": self.mismatch_reasons,
            "ambiguity_score": self.ambiguity_score,
            "feature_snapshot": self.feature_snapshot,
        }


class OrderRecord(Base, TimestampMixin):
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    market_ticker: Mapped[str] = mapped_column(String(128), index=True)
    client_order_id: Mapped[str] = mapped_column(String(255), unique=True)
    kalshi_order_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    signal_id: Mapped[str | None] = mapped_column(ForeignKey("signals.id", ondelete="SET NULL"), nullable=True)
    position_id: Mapped[str | None] = mapped_column(ForeignKey("positions.id", ondelete="SET NULL"), nullable=True)
    side: Mapped[str] = mapped_column(String(16))
    action: Mapped[str] = mapped_column(String(32))
    order_type: Mapped[str] = mapped_column(String(32))
    time_in_force: Mapped[str | None] = mapped_column(String(32), nullable=True)
    post_only: Mapped[bool] = mapped_column(Boolean, default=False)
    reduce_only: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    count: Mapped[int] = mapped_column(Integer)
    price: Mapped[int | None] = mapped_column(Integer, nullable=True)
    yes_price: Mapped[int | None] = mapped_column(Integer, nullable=True)
    no_price: Mapped[int | None] = mapped_column(Integer, nullable=True)
    approval_status: Mapped[str] = mapped_column(String(32), default="not_required")
    requires_manual_approval: Mapped[bool] = mapped_column(Boolean, default=False)
    approved_by_user_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejected_by_user_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    rejected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    preview_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    risk_check_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    canceled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    category: Mapped[str | None] = mapped_column(String(128), nullable=True)
    theme: Mapped[str | None] = mapped_column(String(128), nullable=True)
    size_bucket: Mapped[str | None] = mapped_column(String(32), nullable=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    raw_request: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    raw_response: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "market_ticker": self.market_ticker,
            "client_order_id": self.client_order_id,
            "kalshi_order_id": self.kalshi_order_id,
            "signal_id": self.signal_id,
            "position_id": self.position_id,
            "side": self.side,
            "action": self.action,
            "order_type": self.order_type,
            "time_in_force": self.time_in_force,
            "post_only": self.post_only,
            "reduce_only": self.reduce_only,
            "status": self.status,
            "count": self.count,
            "price": self.price,
            "yes_price": self.yes_price,
            "no_price": self.no_price,
            "approval_status": self.approval_status,
            "requires_manual_approval": self.requires_manual_approval,
            "approved_by_user_id": self.approved_by_user_id,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "rejected_by_user_id": self.rejected_by_user_id,
            "rejected_at": self.rejected_at.isoformat() if self.rejected_at else None,
            "preview_payload": self.preview_payload,
            "risk_check_payload": self.risk_check_payload,
            "submitted_at": self.submitted_at.isoformat() if self.submitted_at else None,
            "canceled_at": self.canceled_at.isoformat() if self.canceled_at else None,
            "category": self.category,
            "theme": self.theme,
            "size_bucket": self.size_bucket,
            "metadata_json": self.metadata_json,
        }


class RiskLimit(Base, TimestampMixin):
    __tablename__ = "risk_limits"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    max_order_count: Mapped[int] = mapped_column(Integer, default=100)
    max_order_notional_cents: Mapped[int] = mapped_column(Integer, default=10_000)
    max_daily_notional_cents: Mapped[int] = mapped_column(Integer, default=100_000)
    max_exposure_per_market_cents: Mapped[int] = mapped_column(Integer, default=25_000)
    max_exposure_per_category_cents: Mapped[int] = mapped_column(Integer, default=75_000)
    max_simultaneous_positions: Mapped[int] = mapped_column(Integer, default=8)
    max_spread_cents: Mapped[int] = mapped_column(Integer, default=12)
    min_liquidity: Mapped[int] = mapped_column(Integer, default=100)
    max_category_concentration: Mapped[float] = mapped_column(Float, default=0.55)
    cooldown_after_loss_minutes: Mapped[int] = mapped_column(Integer, default=90)
    min_time_to_resolution_minutes: Mapped[int] = mapped_column(Integer, default=60)
    overnight_max_spread_cents: Mapped[int] = mapped_column(Integer, default=8)
    overnight_min_liquidity: Mapped[int] = mapped_column(Integer, default=250)
    allowed_markets: Mapped[list[str]] = mapped_column(JSON, default=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "max_order_count": self.max_order_count,
            "max_order_notional_cents": self.max_order_notional_cents,
            "max_daily_notional_cents": self.max_daily_notional_cents,
            "max_exposure_per_market_cents": self.max_exposure_per_market_cents,
            "max_exposure_per_category_cents": self.max_exposure_per_category_cents,
            "max_simultaneous_positions": self.max_simultaneous_positions,
            "max_spread_cents": self.max_spread_cents,
            "min_liquidity": self.min_liquidity,
            "max_category_concentration": self.max_category_concentration,
            "cooldown_after_loss_minutes": self.cooldown_after_loss_minutes,
            "min_time_to_resolution_minutes": self.min_time_to_resolution_minutes,
            "overnight_max_spread_cents": self.overnight_max_spread_cents,
            "overnight_min_liquidity": self.overnight_min_liquidity,
            "allowed_markets": self.allowed_markets,
        }


class PositionRecord(Base, TimestampMixin):
    __tablename__ = "positions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    market_ticker: Mapped[str] = mapped_column(String(128), index=True)
    category: Mapped[str | None] = mapped_column(String(128), nullable=True)
    side: Mapped[str | None] = mapped_column(String(16), nullable=True)
    contracts_count: Mapped[int] = mapped_column(Integer, default=0)
    average_entry_price: Mapped[int] = mapped_column(Integer, default=0)
    exposure_cents: Mapped[int] = mapped_column(Integer, default=0)
    realized_pnl_cents: Mapped[int] = mapped_column(Integer, default=0)
    unrealized_pnl_cents: Mapped[int] = mapped_column(Integer, default=0)
    is_open: Mapped[bool] = mapped_column(Boolean, default=True)
    opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=lambda: datetime.now(timezone.utc))
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "market_ticker": self.market_ticker,
            "category": self.category,
            "side": self.side,
            "contracts_count": self.contracts_count,
            "average_entry_price": self.average_entry_price,
            "exposure_cents": self.exposure_cents,
            "realized_pnl_cents": self.realized_pnl_cents,
            "unrealized_pnl_cents": self.unrealized_pnl_cents,
            "is_open": self.is_open,
            "opened_at": self.opened_at.isoformat() if self.opened_at else None,
            "closed_at": self.closed_at.isoformat() if self.closed_at else None,
            "metadata_json": self.metadata_json,
        }


class FillRecord(Base, TimestampMixin):
    __tablename__ = "fills"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    order_id: Mapped[str | None] = mapped_column(ForeignKey("orders.id", ondelete="SET NULL"), nullable=True, index=True)
    position_id: Mapped[str | None] = mapped_column(ForeignKey("positions.id", ondelete="SET NULL"), nullable=True, index=True)
    kalshi_fill_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    market_ticker: Mapped[str] = mapped_column(String(128), index=True)
    side: Mapped[str | None] = mapped_column(String(16), nullable=True)
    price: Mapped[int] = mapped_column(Integer)
    count: Mapped[int] = mapped_column(Integer)
    fee_cents: Mapped[int] = mapped_column(Integer, default=0)
    filled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "order_id": self.order_id,
            "position_id": self.position_id,
            "kalshi_fill_id": self.kalshi_fill_id,
            "market_ticker": self.market_ticker,
            "side": self.side,
            "price": self.price,
            "count": self.count,
            "fee_cents": self.fee_cents,
            "filled_at": self.filled_at.isoformat() if self.filled_at else None,
            "raw_payload": self.raw_payload,
        }


class ApprovalRequestRecord(Base, TimestampMixin):
    __tablename__ = "approval_requests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    order_id: Mapped[str] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), index=True)
    requested_by_user_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    decided_by_user_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "order_id": self.order_id,
            "requested_by_user_id": self.requested_by_user_id,
            "decided_by_user_id": self.decided_by_user_id,
            "status": self.status,
            "notes": self.notes,
            "decided_at": self.decided_at.isoformat() if self.decided_at else None,
            "created_at": self.created_at.isoformat(),
        }


class RiskEventRecord(Base, TimestampMixin):
    __tablename__ = "risk_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    order_id: Mapped[str | None] = mapped_column(ForeignKey("orders.id", ondelete="SET NULL"), nullable=True, index=True)
    market_ticker: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    severity: Mapped[str] = mapped_column(String(32), default="info")
    rule_name: Mapped[str] = mapped_column(String(128), index=True)
    status: Mapped[str] = mapped_column(String(32), default="recorded")
    detail: Mapped[str] = mapped_column(Text)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "order_id": self.order_id,
            "market_ticker": self.market_ticker,
            "severity": self.severity,
            "rule_name": self.rule_name,
            "status": self.status,
            "detail": self.detail,
            "payload": self.payload,
            "created_at": self.created_at.isoformat(),
        }


class AutomationPolicyRecord(Base, TimestampMixin):
    __tablename__ = "automation_policies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    strategy_id: Mapped[str | None] = mapped_column(ForeignKey("strategies.id", ondelete="SET NULL"), nullable=True, index=True)
    strategy_slug: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    dry_run: Mapped[bool] = mapped_column(Boolean, default=True)
    user_opt_in_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    allowed_market_tickers: Mapped[list[str]] = mapped_column(JSON, default=list)
    allowed_categories: Mapped[list[str]] = mapped_column(JSON, default=list)
    min_confidence_score: Mapped[float] = mapped_column(Float, default=0.9)
    overnight_min_confidence_score: Mapped[float] = mapped_column(Float, default=0.96)
    max_size_bucket: Mapped[str] = mapped_column(String(32), default="small")
    max_open_automated_positions: Mapped[int] = mapped_column(Integer, default=2)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "strategy_id": self.strategy_id,
            "strategy_slug": self.strategy_slug,
            "is_enabled": self.is_enabled,
            "dry_run": self.dry_run,
            "user_opt_in_enabled": self.user_opt_in_enabled,
            "allowed_market_tickers": self.allowed_market_tickers,
            "allowed_categories": self.allowed_categories,
            "min_confidence_score": self.min_confidence_score,
            "overnight_min_confidence_score": self.overnight_min_confidence_score,
            "max_size_bucket": self.max_size_bucket,
            "max_open_automated_positions": self.max_open_automated_positions,
            "notes": self.notes,
        }


class AutomationRunRecord(Base, TimestampMixin):
    __tablename__ = "automation_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    signal_id: Mapped[str] = mapped_column(ForeignKey("signals.id", ondelete="CASCADE"), index=True)
    strategy_id: Mapped[str | None] = mapped_column(ForeignKey("strategies.id", ondelete="SET NULL"), nullable=True, index=True)
    order_id: Mapped[str | None] = mapped_column(ForeignKey("orders.id", ondelete="SET NULL"), nullable=True, index=True)
    policy_id: Mapped[str | None] = mapped_column(ForeignKey("automation_policies.id", ondelete="SET NULL"), nullable=True, index=True)
    mode: Mapped[str] = mapped_column(String(32), default="dry_run")
    status: Mapped[str] = mapped_column(String(64), index=True)
    confidence_score: Mapped[float] = mapped_column(Float)
    decision_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    result_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    kalshi_order_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    anomaly_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "signal_id": self.signal_id,
            "strategy_id": self.strategy_id,
            "order_id": self.order_id,
            "policy_id": self.policy_id,
            "mode": self.mode,
            "status": self.status,
            "confidence_score": self.confidence_score,
            "decision_payload": self.decision_payload,
            "result_payload": self.result_payload,
            "kalshi_order_id": self.kalshi_order_id,
            "anomaly_reason": self.anomaly_reason,
            "created_at": self.created_at.isoformat(),
        }


class AutomationEventRecord(Base, TimestampMixin):
    __tablename__ = "automation_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    run_id: Mapped[str | None] = mapped_column(ForeignKey("automation_runs.id", ondelete="SET NULL"), nullable=True, index=True)
    signal_id: Mapped[str | None] = mapped_column(ForeignKey("signals.id", ondelete="SET NULL"), nullable=True, index=True)
    event_type: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(64), index=True)
    severity: Mapped[str] = mapped_column(String(32), default="info")
    detail: Mapped[str] = mapped_column(Text)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "run_id": self.run_id,
            "signal_id": self.signal_id,
            "event_type": self.event_type,
            "status": self.status,
            "severity": self.severity,
            "detail": self.detail,
            "payload": self.payload,
            "created_at": self.created_at.isoformat(),
        }


class AutomationPauseRecord(Base, TimestampMixin):
    __tablename__ = "automation_pauses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    policy_id: Mapped[str | None] = mapped_column(ForeignKey("automation_policies.id", ondelete="SET NULL"), nullable=True, index=True)
    reason: Mapped[str] = mapped_column(Text)
    triggered_by: Mapped[str] = mapped_column(String(32), default="system")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    resume_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    resumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resumed_by_user_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "policy_id": self.policy_id,
            "reason": self.reason,
            "triggered_by": self.triggered_by,
            "is_active": self.is_active,
            "resume_reason": self.resume_reason,
            "resumed_at": self.resumed_at.isoformat() if self.resumed_at else None,
            "resumed_by_user_id": self.resumed_by_user_id,
            "created_at": self.created_at.isoformat(),
        }


class AutomationFailureRecord(Base, TimestampMixin):
    __tablename__ = "automation_failures"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    run_id: Mapped[str | None] = mapped_column(ForeignKey("automation_runs.id", ondelete="SET NULL"), nullable=True, index=True)
    policy_id: Mapped[str | None] = mapped_column(ForeignKey("automation_policies.id", ondelete="SET NULL"), nullable=True, index=True)
    failure_type: Mapped[str] = mapped_column(String(64), index=True)
    detail: Mapped[str] = mapped_column(Text)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "run_id": self.run_id,
            "policy_id": self.policy_id,
            "failure_type": self.failure_type,
            "detail": self.detail,
            "payload": self.payload,
            "is_resolved": self.is_resolved,
            "created_at": self.created_at.isoformat(),
        }


class NotificationEndpoint(Base, TimestampMixin):
    __tablename__ = "notification_endpoints"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    channel: Mapped[str] = mapped_column(String(32))
    destination: Mapped[str] = mapped_column(String(512))
    title_prefix: Mapped[str | None] = mapped_column(String(128), nullable=True)
    device_target: Mapped[str | None] = mapped_column(String(255), nullable=True)
    provider: Mapped[str] = mapped_column(String(32), default="pushover")
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    filters_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    quiet_hours_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    supports_pwa_push: Mapped[bool] = mapped_column(Boolean, default=False)
    overnight_critical_only: Mapped[bool] = mapped_column(Boolean, default=True)
    allow_daytime_info: Mapped[bool] = mapped_column(Boolean, default=True)
    allow_emergency_priority: Mapped[bool] = mapped_column(Boolean, default=False)
    default_deep_link_base: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "channel": self.channel,
            "destination": self.destination,
            "title_prefix": self.title_prefix,
            "device_target": self.device_target,
            "provider": self.provider,
            "is_enabled": self.is_enabled,
            "filters_json": self.filters_json,
            "quiet_hours_enabled": self.quiet_hours_enabled,
            "supports_pwa_push": self.supports_pwa_push,
            "overnight_critical_only": self.overnight_critical_only,
            "allow_daytime_info": self.allow_daytime_info,
            "allow_emergency_priority": self.allow_emergency_priority,
            "default_deep_link_base": self.default_deep_link_base,
        }


class NotificationDeliveryRecord(Base, TimestampMixin):
    __tablename__ = "notification_deliveries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    endpoint_id: Mapped[str | None] = mapped_column(ForeignKey("notification_endpoints.id"), nullable=True)
    provider: Mapped[str] = mapped_column(String(32), default="pushover")
    dedupe_key: Mapped[str] = mapped_column(String(255), index=True)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    title: Mapped[str] = mapped_column(String(255))
    message: Mapped[str] = mapped_column(Text)
    deep_link_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    provider_receipt: Mapped[str | None] = mapped_column(String(255), nullable=True)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    urgency: Mapped[str | None] = mapped_column(String(32), nullable=True)
    overnight_flag: Mapped[bool] = mapped_column(Boolean, default=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    quiet_hours_suppressed: Mapped[bool] = mapped_column(Boolean, default=False)
    dedupe_suppressed: Mapped[bool] = mapped_column(Boolean, default=False)
    signal_id: Mapped[str | None] = mapped_column(ForeignKey("signals.id", ondelete="SET NULL"), nullable=True)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "endpoint_id": self.endpoint_id,
            "provider": self.provider,
            "dedupe_key": self.dedupe_key,
            "status": self.status,
            "title": self.title,
            "message": self.message,
            "deep_link_url": self.deep_link_url,
            "provider_receipt": self.provider_receipt,
            "attempt_count": self.attempt_count,
            "last_error": self.last_error,
            "payload": self.payload,
            "priority": self.priority,
            "urgency": self.urgency,
            "overnight_flag": self.overnight_flag,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "quiet_hours_suppressed": self.quiet_hours_suppressed,
            "dedupe_suppressed": self.dedupe_suppressed,
            "signal_id": self.signal_id,
        }


class NotificationAuditLogRecord(Base, TimestampMixin):
    __tablename__ = "notification_audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    delivery_id: Mapped[str | None] = mapped_column(ForeignKey("notification_deliveries.id", ondelete="SET NULL"), nullable=True, index=True)
    signal_id: Mapped[str | None] = mapped_column(ForeignKey("signals.id", ondelete="SET NULL"), nullable=True, index=True)
    event_type: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(32), default="recorded")
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "delivery_id": self.delivery_id,
            "signal_id": self.signal_id,
            "event_type": self.event_type,
            "status": self.status,
            "detail": self.detail,
            "payload": self.payload,
            "created_at": self.created_at.isoformat(),
        }


class NotificationReceiptRecord(Base, TimestampMixin):
    __tablename__ = "notification_receipts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    delivery_id: Mapped[str] = mapped_column(ForeignKey("notification_deliveries.id", ondelete="CASCADE"), index=True)
    provider: Mapped[str] = mapped_column(String(32), default="pushover")
    receipt: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(32), default="active")
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "delivery_id": self.delivery_id,
            "provider": self.provider,
            "receipt": self.receipt,
            "status": self.status,
            "last_checked_at": self.last_checked_at.isoformat() if self.last_checked_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "payload": self.payload,
        }


class QuietHourPolicyRecord(Base, TimestampMixin):
    __tablename__ = "quiet_hour_policies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    timezone_name: Mapped[str] = mapped_column(String(64), default="America/New_York")
    quiet_start_hour: Mapped[int] = mapped_column(Integer, default=22)
    quiet_end_hour: Mapped[int] = mapped_column(Integer, default=7)
    allow_critical_overnight: Mapped[bool] = mapped_column(Boolean, default=True)
    allow_daytime_info: Mapped[bool] = mapped_column(Boolean, default=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "timezone_name": self.timezone_name,
            "quiet_start_hour": self.quiet_start_hour,
            "quiet_end_hour": self.quiet_end_hour,
            "allow_critical_overnight": self.allow_critical_overnight,
            "allow_daytime_info": self.allow_daytime_info,
            "is_enabled": self.is_enabled,
        }


class UserDeviceTargetRecord(Base, TimestampMixin):
    __tablename__ = "user_device_targets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    provider: Mapped[str] = mapped_column(String(32), default="pushover")
    device_name: Mapped[str] = mapped_column(String(255))
    destination: Mapped[str] = mapped_column(String(512))
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "provider": self.provider,
            "device_name": self.device_name,
            "destination": self.destination,
            "is_primary": self.is_primary,
            "is_enabled": self.is_enabled,
            "metadata_json": self.metadata_json,
        }


class ExecutionAuditRecord(Base, TimestampMixin):
    __tablename__ = "execution_audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    order_id: Mapped[str | None] = mapped_column(ForeignKey("orders.id"), nullable=True)
    actor_user_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    event_type: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(32), default="recorded")
    detail: Mapped[str] = mapped_column(Text)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "order_id": self.order_id,
            "actor_user_id": self.actor_user_id,
            "event_type": self.event_type,
            "status": self.status,
            "detail": self.detail,
            "payload": self.payload,
            "created_at": self.created_at.isoformat(),
        }


class SystemControlRecord(Base, TimestampMixin):
    __tablename__ = "system_controls"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_by_user_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "is_enabled": self.is_enabled,
            "reason": self.reason,
            "updated_by_user_id": self.updated_by_user_id,
            "updated_at": self.updated_at.isoformat(),
        }


class SimulationRunRecord(Base, TimestampMixin):
    __tablename__ = "simulation_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(255), index=True)
    mode: Mapped[str] = mapped_column(String(32), default="replay")
    status: Mapped[str] = mapped_column(String(32), default="created")
    market_ticker: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    config_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    summary_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "mode": self.mode,
            "status": self.status,
            "market_ticker": self.market_ticker,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "config_json": self.config_json,
            "summary_json": self.summary_json,
            "created_at": self.created_at.isoformat(),
        }


class PaperOrderRecord(Base, TimestampMixin):
    __tablename__ = "paper_orders"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    source_order_id: Mapped[str | None] = mapped_column(ForeignKey("orders.id", ondelete="SET NULL"), nullable=True, index=True)
    signal_id: Mapped[str | None] = mapped_column(ForeignKey("signals.id", ondelete="SET NULL"), nullable=True, index=True)
    market_ticker: Mapped[str] = mapped_column(String(128), index=True)
    side: Mapped[str] = mapped_column(String(16))
    action: Mapped[str] = mapped_column(String(32))
    order_type: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(32), default="submitted")
    requested_count: Mapped[int] = mapped_column(Integer)
    filled_count: Mapped[int] = mapped_column(Integer, default=0)
    remaining_count: Mapped[int] = mapped_column(Integer, default=0)
    reference_price: Mapped[int | None] = mapped_column(Integer, nullable=True)
    simulated_average_fill_price: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fill_mode: Mapped[str] = mapped_column(String(32), default="midpoint")
    is_automation: Mapped[bool] = mapped_column(Boolean, default=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "source_order_id": self.source_order_id,
            "signal_id": self.signal_id,
            "market_ticker": self.market_ticker,
            "side": self.side,
            "action": self.action,
            "order_type": self.order_type,
            "status": self.status,
            "requested_count": self.requested_count,
            "filled_count": self.filled_count,
            "remaining_count": self.remaining_count,
            "reference_price": self.reference_price,
            "simulated_average_fill_price": self.simulated_average_fill_price,
            "fill_mode": self.fill_mode,
            "is_automation": self.is_automation,
            "metadata_json": self.metadata_json,
            "created_at": self.created_at.isoformat(),
        }


class PaperFillRecord(Base, TimestampMixin):
    __tablename__ = "paper_fills"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    paper_order_id: Mapped[str] = mapped_column(ForeignKey("paper_orders.id", ondelete="CASCADE"), index=True)
    market_ticker: Mapped[str] = mapped_column(String(128), index=True)
    side: Mapped[str | None] = mapped_column(String(16), nullable=True)
    price: Mapped[int] = mapped_column(Integer)
    count: Mapped[int] = mapped_column(Integer)
    fee_cents: Mapped[int] = mapped_column(Integer, default=0)
    simulated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "paper_order_id": self.paper_order_id,
            "market_ticker": self.market_ticker,
            "side": self.side,
            "price": self.price,
            "count": self.count,
            "fee_cents": self.fee_cents,
            "simulated_at": self.simulated_at.isoformat() if self.simulated_at else None,
            "metadata_json": self.metadata_json,
        }


class PaperPositionRecord(Base, TimestampMixin):
    __tablename__ = "paper_positions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    signal_id: Mapped[str | None] = mapped_column(ForeignKey("signals.id", ondelete="SET NULL"), nullable=True, index=True)
    market_ticker: Mapped[str] = mapped_column(String(128), index=True)
    category: Mapped[str | None] = mapped_column(String(128), nullable=True)
    side: Mapped[str | None] = mapped_column(String(16), nullable=True)
    contracts_count: Mapped[int] = mapped_column(Integer, default=0)
    average_entry_price: Mapped[int] = mapped_column(Integer, default=0)
    exposure_cents: Mapped[int] = mapped_column(Integer, default=0)
    realized_pnl_cents: Mapped[int] = mapped_column(Integer, default=0)
    unrealized_pnl_cents: Mapped[int] = mapped_column(Integer, default=0)
    entry_confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_open: Mapped[bool] = mapped_column(Boolean, default=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "signal_id": self.signal_id,
            "market_ticker": self.market_ticker,
            "category": self.category,
            "side": self.side,
            "contracts_count": self.contracts_count,
            "average_entry_price": self.average_entry_price,
            "exposure_cents": self.exposure_cents,
            "realized_pnl_cents": self.realized_pnl_cents,
            "unrealized_pnl_cents": self.unrealized_pnl_cents,
            "entry_confidence_score": self.entry_confidence_score,
            "is_open": self.is_open,
            "closed_at": self.closed_at.isoformat() if self.closed_at else None,
            "metadata_json": self.metadata_json,
            "created_at": self.created_at.isoformat(),
        }


class PaperPortfolioSnapshotRecord(Base, TimestampMixin):
    __tablename__ = "paper_portfolio_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    cash_cents: Mapped[int] = mapped_column(Integer, default=0)
    equity_cents: Mapped[int] = mapped_column(Integer, default=0)
    realized_pnl_cents: Mapped[int] = mapped_column(Integer, default=0)
    unrealized_pnl_cents: Mapped[int] = mapped_column(Integer, default=0)
    exposure_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "cash_cents": self.cash_cents,
            "equity_cents": self.equity_cents,
            "realized_pnl_cents": self.realized_pnl_cents,
            "unrealized_pnl_cents": self.unrealized_pnl_cents,
            "exposure_json": self.exposure_json,
            "metadata_json": self.metadata_json,
            "created_at": self.created_at.isoformat(),
        }
