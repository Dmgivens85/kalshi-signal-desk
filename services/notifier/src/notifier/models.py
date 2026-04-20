from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class NotificationCandidate(BaseModel):
    signal_id: str | None = None
    market_ticker: str | None = None
    title: str
    message: str
    deep_link: str
    urgency: str
    dedupe_key: str
    expiration_time: datetime | None = None
    overnight_flag: bool = False
    classification: str | None = None
    confidence_score: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class NotificationMessage(BaseModel):
    token: str | None = None
    user: str | None = None
    message: str
    title: str | None = None
    device: str | None = None
    url: str | None = None
    url_title: str | None = None
    priority: int = 0
    sound: str | None = None
    retry: int | None = None
    expire: int | None = None
    provider: str = "pushover"


class DeliveryResult(BaseModel):
    delivery_id: str | None = None
    status: str
    provider: str
    provider_message: str | None = None
    receipt: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class DeliveryAttempt(BaseModel):
    attempt_number: int
    started_at: datetime
    completed_at: datetime | None = None
    status: str
    error: str | None = None


class QuietHoursRule(BaseModel):
    timezone_name: str = "America/New_York"
    quiet_start_hour: int = 22
    quiet_end_hour: int = 7
    allow_critical_overnight: bool = True
    allow_daytime_info: bool = True
    is_enabled: bool = True


class DeliveryPolicy(BaseModel):
    should_send: bool
    reason: str
    priority: int = 0
    use_emergency: bool = False
    retry_seconds: int | None = None
    expire_seconds: int | None = None
    quiet_hours_bypass: bool = False
    classification: str = "digest_only"


class ReceiptTracking(BaseModel):
    delivery_id: str
    receipt: str
    provider: str = "pushover"
    expires_at: datetime | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class NotificationAuditRecord(BaseModel):
    delivery_id: str | None = None
    signal_id: str | None = None
    event_type: str
    status: str
    detail: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
