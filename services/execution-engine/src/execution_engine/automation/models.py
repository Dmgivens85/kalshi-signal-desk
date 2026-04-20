from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class AutomationDecision(StrEnum):
    MANUAL_REVIEW_REQUIRED = "manual_review_required"
    AUTOMATION_ALLOWED = "automation_allowed"
    AUTOMATION_BLOCKED = "automation_blocked"
    AUTOMATION_PAUSED = "automation_paused"
    AUTOMATION_DISABLED_DUE_TO_ANOMALY = "automation_disabled_due_to_anomaly"


class AutomationPolicyInput(BaseModel):
    name: str
    strategy_id: str | None = None
    strategy_slug: str | None = None
    enabled: bool = False
    dry_run: bool = True
    user_opt_in_enabled: bool = False
    allowed_market_tickers: list[str] = Field(default_factory=list)
    allowed_categories: list[str] = Field(default_factory=list)
    min_confidence_score: float = 0.9
    overnight_min_confidence_score: float = 0.96
    max_size_bucket: str = "small"
    max_open_automated_positions: int = 2
    notes: str | None = None


class AutomationEligibility(BaseModel):
    decision: AutomationDecision
    reasons: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    policy_id: str | None = None
    dry_run: bool = True
    anomaly_detected: bool = False


class AutomationRunContext(BaseModel):
    signal_id: str
    strategy_id: str | None = None
    strategy_slug: str | None = None
    market_ticker: str
    confidence_score: float
    overnight_flag: bool = False
    suggested_size_bucket: str | None = None
    category: str | None = None


class AutomationStatusSnapshot(BaseModel):
    global_enabled: bool
    global_paused: bool
    global_dry_run: bool
    blocked_reason: str | None = None
    active_policy_count: int = 0
    recent_events: list[dict[str, Any]] = Field(default_factory=list)
    recent_failures: list[dict[str, Any]] = Field(default_factory=list)


class AutomationAuditPayload(BaseModel):
    signal_id: str
    strategy_id: str | None = None
    strategy_name: str | None = None
    confidence_score: float
    risk_evaluation_result: dict[str, Any] = Field(default_factory=dict)
    eligibility_decision: str
    final_submission_result: dict[str, Any] = Field(default_factory=dict)
    kalshi_response_ids: dict[str, Any] = Field(default_factory=dict)
    anomaly_reason: str | None = None


class AutomationAnomaly(BaseModel):
    triggered: bool
    reason: str | None = None
    detail: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    observed_at: datetime | None = None
