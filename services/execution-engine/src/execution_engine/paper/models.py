from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class ExecutionMode(StrEnum):
    DISABLED = "disabled"
    PAPER = "paper"
    LIVE = "live"


class PaperFillMode(StrEnum):
    MIDPOINT = "midpoint"
    AGGRESSIVE = "aggressive"
    PASSIVE = "passive"


class PaperOrderOutcome(BaseModel):
    order_id: str
    status: str
    filled_count: int = 0
    remaining_count: int = 0
    average_fill_price: int | None = None
    simulated: bool = True
    fill_mode: str
    payload: dict[str, Any] = Field(default_factory=dict)


class PaperPerformanceSnapshot(BaseModel):
    open_positions: int
    closed_positions: int
    realized_pnl_cents: int
    unrealized_pnl_cents: int
    exposure_by_market: dict[str, int] = Field(default_factory=dict)
    exposure_by_category: dict[str, int] = Field(default_factory=dict)
    win_rate: float = 0.0
    average_confidence: float = 0.0


class ReplayRequest(BaseModel):
    name: str
    market_ticker: str | None = None
    start_at: datetime | None = None
    end_at: datetime | None = None
    max_events: int = 500


class ReplayResult(BaseModel):
    run_id: str
    status: str
    processed_events: int
    processed_signals: int
    summary: dict[str, Any] = Field(default_factory=dict)
