from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class ApprovalStatus(StrEnum):
    PROPOSED = "proposed"
    BLOCKED = "blocked"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUBMITTED = "submitted"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELED = "canceled"
    EXPIRED = "expired"


class SuggestedAction(StrEnum):
    WATCH = "watch"
    APPROVE = "approve"
    REDUCE = "reduce"
    BLOCK = "block"
    SUBMIT = "submit"


class SizeBucket(StrEnum):
    MICRO = "micro"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


class RiskCheckResult(BaseModel):
    rule: str
    passed: bool
    blocking: bool = False
    detail: str
    observed_value: float | int | str | None = None
    limit_value: float | int | str | None = None


class ExposureImpact(BaseModel):
    market_ticker: str
    category: str
    current_market_exposure_cents: int = 0
    projected_market_exposure_cents: int = 0
    current_category_exposure_cents: int = 0
    projected_category_exposure_cents: int = 0
    open_positions_count: int = 0


class RiskEvaluation(BaseModel):
    passed: bool
    blocking_reasons: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    checks: list[RiskCheckResult] = Field(default_factory=list)
    exposure_impact: ExposureImpact
    size_recommendation: SizeBucket
    manual_approval_allowed: bool = True
    overnight_adjusted: bool = False


class MarketConditions(BaseModel):
    last_price: int | None = None
    best_bid: int | None = None
    best_ask: int | None = None
    spread_cents: int | None = None
    liquidity: int | None = None
    volume: int | None = None
    time_to_resolution_minutes: int | None = None


class TradeCandidate(BaseModel):
    signal_id: str | None = None
    market_ticker: str
    side: str
    action: str
    count: int
    yes_price: int | None = None
    no_price: int | None = None
    order_type: str = "limit"
    time_in_force: str | None = "day"
    post_only: bool = False
    reduce_only: bool = False
    category: str = "general"
    theme: str = "general"
    overnight_flag: bool = False
    signal_summary: str | None = None
    confidence_score: float | None = None
    evidence_refs: list[dict[str, Any]] = Field(default_factory=list)


class OrderPreview(BaseModel):
    ticker: str
    side: str
    action: str
    size_suggestion: SizeBucket
    suggested_count: int
    indicative_price_data: MarketConditions
    supporting_signal_summary: str | None = None
    risk_evaluation_summary: str
    recommended_next_action: SuggestedAction
    approval_status: ApprovalStatus
    risk_evaluation: RiskEvaluation
    candidate_order: dict[str, Any]


class ApprovalDecision(BaseModel):
    order_id: str
    actor_user_id: str | None = None
    notes: str | None = None
    decided_at: datetime
    status: ApprovalStatus


class ReconciliationUpdate(BaseModel):
    order_id: str
    kalshi_order_id: str | None = None
    status: ApprovalStatus | str
    fill_count: int = 0
    fill_price: int | None = None
    raw_payload: dict[str, Any] = Field(default_factory=dict)


class PendingApprovalItem(BaseModel):
    order_id: str
    market_ticker: str
    status: ApprovalStatus
    size_bucket: SizeBucket
    reason_summary: str
    created_at: datetime


class RiskStatusSnapshot(BaseModel):
    kill_switch_enabled: bool
    current_open_positions: int
    current_market_exposure_cents: int
    current_category_exposure_cents: dict[str, int]
    latest_risk_events: list[dict[str, Any]] = Field(default_factory=list)
