from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    KalshiMarket,
    MarketSnapshot,
    OrderRecord,
    PositionRecord,
    RiskEventRecord,
    SystemControlRecord,
)
from execution_engine.config import ExecutionEngineSettings
from execution_engine.models import ExposureImpact, RiskCheckResult, RiskEvaluation, SizeBucket, TradeCandidate


class DeterministicRiskEngine:
    KILL_SWITCH_ID = "global_trading"

    def __init__(self, settings: ExecutionEngineSettings, db: AsyncSession) -> None:
        self.settings = settings
        self.db = db

    async def ensure_kill_switch(self) -> SystemControlRecord:
        row = (
            await self.db.execute(select(SystemControlRecord).where(SystemControlRecord.id == self.KILL_SWITCH_ID))
        ).scalar_one_or_none()
        if row is None:
            row = SystemControlRecord(id=self.KILL_SWITCH_ID, is_enabled=True, reason="Initialized")
            self.db.add(row)
            await self.db.flush()
        return row

    async def evaluate(self, candidate: TradeCandidate) -> RiskEvaluation:
        kill_switch = await self.ensure_kill_switch()
        snapshot = await self._latest_snapshot(candidate.market_ticker)
        category = await self._category_for_market(candidate.market_ticker, candidate.category)
        market_exposure, category_exposure, open_positions = await self._current_exposure(candidate.market_ticker, category)
        daily_loss = await self._daily_loss_cents()
        cooldown_active = await self._cooldown_active()
        concentration = (category_exposure / max(1, category_exposure + market_exposure)) if (category_exposure + market_exposure) else 0.0
        projected_market = market_exposure + self._estimate_notional(candidate)
        projected_category = category_exposure + self._estimate_notional(candidate)

        checks: list[RiskCheckResult] = []
        blocking: list[str] = []
        warnings: list[str] = []

        def record(rule: str, passed: bool, detail: str, *, blocking_rule: bool = True, observed: object = None, limit: object = None) -> None:
            checks.append(
                RiskCheckResult(
                    rule=rule,
                    passed=passed,
                    blocking=blocking_rule and not passed,
                    detail=detail,
                    observed_value=observed,
                    limit_value=limit,
                )
            )
            if not passed:
                if blocking_rule:
                    blocking.append(detail)
                else:
                    warnings.append(detail)

        record(
            "global_kill_switch",
            kill_switch.is_enabled,
            kill_switch.reason or "Trading disabled by global kill switch." if not kill_switch.is_enabled else "Trading enabled.",
        )
        record(
            "max_exposure_per_market",
            projected_market <= self.settings.max_exposure_per_market_cents,
            f"Projected market exposure {projected_market}c exceeds limit {self.settings.max_exposure_per_market_cents}c.",
            observed=projected_market,
            limit=self.settings.max_exposure_per_market_cents,
        )
        record(
            "max_exposure_per_category",
            projected_category <= self.settings.max_exposure_per_category_cents,
            f"Projected category exposure {projected_category}c exceeds limit {self.settings.max_exposure_per_category_cents}c.",
            observed=projected_category,
            limit=self.settings.max_exposure_per_category_cents,
        )
        record(
            "max_daily_drawdown",
            daily_loss <= self.settings.max_daily_drawdown_cents,
            f"Daily drawdown {daily_loss}c exceeds limit {self.settings.max_daily_drawdown_cents}c.",
            observed=daily_loss,
            limit=self.settings.max_daily_drawdown_cents,
        )
        record(
            "max_simultaneous_positions",
            open_positions < self.settings.max_simultaneous_positions,
            f"Open positions {open_positions} exceeds limit {self.settings.max_simultaneous_positions}.",
            observed=open_positions,
            limit=self.settings.max_simultaneous_positions,
        )

        spread_limit = self.settings.overnight_max_spread_cents if candidate.overnight_flag and self.settings.overnight_mode_enabled else self.settings.max_spread_cents
        liquidity_limit = self.settings.overnight_min_liquidity if candidate.overnight_flag and self.settings.overnight_mode_enabled else self.settings.min_liquidity
        spread = snapshot.get("spread_cents")
        liquidity = snapshot.get("liquidity")
        time_to_resolution = snapshot.get("time_to_resolution_minutes")

        record(
            "spread_threshold",
            spread is None or spread <= spread_limit,
            f"Spread {spread}c exceeds limit {spread_limit}c.",
            observed=spread,
            limit=spread_limit,
        )
        record(
            "liquidity_floor",
            liquidity is None or liquidity >= liquidity_limit,
            f"Liquidity {liquidity} is below floor {liquidity_limit}.",
            observed=liquidity,
            limit=liquidity_limit,
        )
        record(
            "correlation_concentration",
            concentration <= self.settings.max_category_concentration,
            f"Category concentration {concentration:.2f} exceeds limit {self.settings.max_category_concentration:.2f}.",
            blocking_rule=False,
            observed=round(concentration, 4),
            limit=self.settings.max_category_concentration,
        )
        record(
            "cooldown_after_losses",
            not cooldown_active,
            "Cooldown after recent losses is still active.",
            observed=str(cooldown_active),
            limit=False,
        )
        record(
            "time_to_resolution",
            time_to_resolution is None or time_to_resolution >= self.settings.min_time_to_resolution_minutes,
            f"Time to resolution {time_to_resolution}m is below minimum {self.settings.min_time_to_resolution_minutes}m.",
            observed=time_to_resolution,
            limit=self.settings.min_time_to_resolution_minutes,
        )
        if candidate.overnight_flag and self.settings.overnight_mode_enabled:
            record(
                "overnight_manual_only",
                True,
                "Overnight mode uses stricter spread and liquidity limits.",
                blocking_rule=False,
            )

        size = self._size_bucket(candidate.count)
        exposure_impact = ExposureImpact(
            market_ticker=candidate.market_ticker,
            category=category,
            current_market_exposure_cents=market_exposure,
            projected_market_exposure_cents=projected_market,
            current_category_exposure_cents=category_exposure,
            projected_category_exposure_cents=projected_category,
            open_positions_count=open_positions,
        )
        return RiskEvaluation(
            passed=not blocking,
            blocking_reasons=blocking,
            warnings=warnings,
            checks=checks,
            exposure_impact=exposure_impact,
            size_recommendation=size,
            manual_approval_allowed=not any(check.rule == "global_kill_switch" and not check.passed for check in checks),
            overnight_adjusted=bool(candidate.overnight_flag and self.settings.overnight_mode_enabled),
        )

    async def summary(self) -> dict[str, object]:
        latest_events = list(
            (
                await self.db.execute(select(RiskEventRecord).order_by(desc(RiskEventRecord.created_at)).limit(10))
            ).scalars().all()
        )
        positions = list((await self.db.execute(select(PositionRecord).where(PositionRecord.is_open.is_(True)))).scalars().all())
        by_category: dict[str, int] = defaultdict(int)
        for position in positions:
            by_category[position.category or "general"] += position.exposure_cents
        kill_switch = await self.ensure_kill_switch()
        return {
            "kill_switch_enabled": kill_switch.is_enabled,
            "current_open_positions": len(positions),
            "current_market_exposure_cents": sum(position.exposure_cents for position in positions),
            "current_category_exposure_cents": dict(by_category),
            "latest_risk_events": [item.to_dict() for item in latest_events],
        }

    async def _latest_snapshot(self, ticker: str) -> dict[str, int | None]:
        row = (
            await self.db.execute(
                select(MarketSnapshot).where(MarketSnapshot.market_ticker == ticker).order_by(desc(MarketSnapshot.observed_at))
            )
        ).scalar_one_or_none()
        if row is None:
            return {"spread_cents": None, "liquidity": None, "time_to_resolution_minutes": None}
        spread = None
        if row.yes_bid is not None and row.yes_ask is not None:
            spread = max(0, row.yes_ask - row.yes_bid)
        time_to_resolution = None
        if row.close_time:
            time_to_resolution = max(0, int((row.close_time - datetime.now(timezone.utc)).total_seconds() / 60))
        return {
            "spread_cents": spread,
            "liquidity": row.liquidity,
            "time_to_resolution_minutes": time_to_resolution,
        }

    async def _category_for_market(self, ticker: str, fallback: str) -> str:
        row = await self.db.get(KalshiMarket, ticker)
        if row and row.series_ticker:
            return row.series_ticker.split("-")[0].lower()
        return fallback or ticker.split("-")[0].lower()

    async def _current_exposure(self, ticker: str, category: str) -> tuple[int, int, int]:
        positions = list((await self.db.execute(select(PositionRecord).where(PositionRecord.is_open.is_(True)))).scalars().all())
        market_exposure = sum(position.exposure_cents for position in positions if position.market_ticker == ticker)
        category_exposure = sum(position.exposure_cents for position in positions if (position.category or "general") == category)
        open_positions = len(positions)
        return market_exposure, category_exposure, open_positions

    async def _daily_loss_cents(self) -> int:
        cutoff = datetime.now(timezone.utc) - timedelta(days=1)
        closed = list(
            (
                await self.db.execute(
                    select(PositionRecord).where(PositionRecord.closed_at.is_not(None), PositionRecord.closed_at >= cutoff)
                )
            ).scalars().all()
        )
        losses = [abs(position.realized_pnl_cents) for position in closed if position.realized_pnl_cents < 0]
        return sum(losses)

    async def _cooldown_active(self) -> bool:
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=self.settings.cooldown_after_loss_minutes)
        recent_loss = (
            await self.db.execute(
                select(PositionRecord)
                .where(PositionRecord.closed_at.is_not(None), PositionRecord.closed_at >= cutoff, PositionRecord.realized_pnl_cents < 0)
                .order_by(desc(PositionRecord.closed_at))
            )
        ).scalar_one_or_none()
        return recent_loss is not None

    def _estimate_notional(self, candidate: TradeCandidate) -> int:
        price = candidate.yes_price if candidate.yes_price is not None else candidate.no_price
        return int(price or 50) * int(candidate.count)

    def _size_bucket(self, count: int) -> SizeBucket:
        if count <= 5:
            return SizeBucket.MICRO
        if count <= 15:
            return SizeBucket.SMALL
        if count <= 40:
            return SizeBucket.MEDIUM
        return SizeBucket.LARGE
