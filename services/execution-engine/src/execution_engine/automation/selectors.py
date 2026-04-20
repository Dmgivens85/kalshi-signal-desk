from __future__ import annotations

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AutomationPolicyRecord, SignalRecord, StrategyRecord


class AutomationSelector:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def active_policies(self) -> list[AutomationPolicyRecord]:
        return list(
            (
                await self.db.execute(
                    select(AutomationPolicyRecord).where(AutomationPolicyRecord.is_enabled.is_(True)).order_by(desc(AutomationPolicyRecord.created_at))
                )
            ).scalars().all()
        )

    async def strategy_for_signal(self, signal: SignalRecord) -> StrategyRecord | None:
        if not signal.strategy_id:
            return None
        return await self.db.get(StrategyRecord, signal.strategy_id)

    async def policy_for_signal(self, signal: SignalRecord, strategy: StrategyRecord | None) -> AutomationPolicyRecord | None:
        policies = await self.active_policies()
        for policy in policies:
            if policy.strategy_id and signal.strategy_id != policy.strategy_id:
                continue
            if policy.strategy_slug and strategy and policy.strategy_slug != strategy.slug:
                continue
            if policy.allowed_market_tickers and signal.market_ticker not in policy.allowed_market_tickers:
                continue
            if policy.allowed_categories:
                category = (strategy.slug if strategy else signal.market_ticker.split("-")[0].lower()) if policy.allowed_categories else None
                if category not in policy.allowed_categories:
                    continue
            return policy
        return None
