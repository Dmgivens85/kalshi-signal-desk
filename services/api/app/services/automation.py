from __future__ import annotations

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import APISettings
from app.db.models import (
    AutomationEventRecord,
    AutomationFailureRecord,
    AutomationPauseRecord,
    AutomationPolicyRecord,
    StrategyRecord,
)
from app.services.execution import GuardedExecutionService
from execution_engine.automation import AutomationRunner, AutomationSettings
from execution_engine.automation.models import AutomationPolicyInput
from kalshi_client import KalshiHttpClient


class AutomationService:
    def __init__(self, settings: APISettings, db: AsyncSession, kalshi: KalshiHttpClient) -> None:
        self.settings = settings
        self.db = db
        self.execution = GuardedExecutionService(settings, db, kalshi)
        self.runner = AutomationRunner(AutomationSettings(), db, self.execution)

    async def status(self) -> dict[str, object]:
        return (await self.runner.status()).model_dump(mode="json")

    async def list_policies(self) -> dict[str, object]:
        result = await self.db.execute(select(AutomationPolicyRecord).order_by(desc(AutomationPolicyRecord.created_at)))
        return {"items": [item.to_dict() for item in result.scalars().all()]}

    async def upsert_policy(self, payload: AutomationPolicyInput) -> dict[str, object]:
        result = await self.db.execute(select(AutomationPolicyRecord).where(AutomationPolicyRecord.name == payload.name))
        record = result.scalar_one_or_none()
        strategy_id = payload.strategy_id
        if payload.strategy_slug and not strategy_id:
            strategy = (
                await self.db.execute(select(StrategyRecord).where(StrategyRecord.slug == payload.strategy_slug))
            ).scalar_one_or_none()
            strategy_id = strategy.id if strategy else None
        if record is None:
            record = AutomationPolicyRecord(name=payload.name)
            self.db.add(record)
        field_map = {"enabled": "is_enabled"}
        for key, value in payload.model_dump().items():
            target_key = field_map.get(key, key)
            if target_key == "strategy_id":
                setattr(record, target_key, strategy_id)
            else:
                setattr(record, target_key, value)
        await self.db.commit()
        await self.db.refresh(record)
        return record.to_dict()

    async def enable(self, actor_user_id: str | None) -> dict[str, object]:
        return await self.runner.enable(actor_user_id)

    async def disable(self, actor_user_id: str | None, reason: str | None = None) -> dict[str, object]:
        return await self.runner.disable(actor_user_id, reason)

    async def pause(self, actor_user_id: str | None, reason: str) -> dict[str, object]:
        return await self.runner.pause(actor_user_id, reason)

    async def resume(self, actor_user_id: str | None, reason: str | None = None) -> dict[str, object]:
        return await self.runner.resume(actor_user_id, reason)

    async def list_events(self) -> dict[str, object]:
        result = await self.db.execute(select(AutomationEventRecord).order_by(desc(AutomationEventRecord.created_at)))
        return {"items": [item.to_dict() for item in result.scalars().all()]}

    async def list_failures(self) -> dict[str, object]:
        result = await self.db.execute(select(AutomationFailureRecord).order_by(desc(AutomationFailureRecord.created_at)))
        return {"items": [item.to_dict() for item in result.scalars().all()]}

    async def list_pauses(self) -> dict[str, object]:
        result = await self.db.execute(select(AutomationPauseRecord).order_by(desc(AutomationPauseRecord.created_at)))
        return {"items": [item.to_dict() for item in result.scalars().all()]}

    async def evaluate_once(self, limit: int = 10) -> dict[str, object]:
        return await self.runner.evaluate_pending_signals(limit=limit)
