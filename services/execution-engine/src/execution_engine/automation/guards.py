from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AutomationPauseRecord, OrderRecord, PositionRecord, ServiceHealthEvent, SystemControlRecord
from execution_engine.automation.config import AutomationSettings


class AutomationGuardSet:
    GLOBAL_ID = "selective_automation"
    KILL_SWITCH_ID = "global_trading"

    def __init__(self, settings: AutomationSettings, db: AsyncSession) -> None:
        self.settings = settings
        self.db = db

    async def ensure_global_control(self) -> SystemControlRecord:
        row = (
            await self.db.execute(select(SystemControlRecord).where(SystemControlRecord.id == self.GLOBAL_ID))
        ).scalar_one_or_none()
        if row is None:
            row = SystemControlRecord(id=self.GLOBAL_ID, is_enabled=self.settings.enabled_by_default, reason="Automation disabled by default")
            self.db.add(row)
            await self.db.flush()
        return row

    async def ensure_kill_switch(self) -> SystemControlRecord:
        row = (
            await self.db.execute(select(SystemControlRecord).where(SystemControlRecord.id == self.KILL_SWITCH_ID))
        ).scalar_one_or_none()
        if row is None:
            row = SystemControlRecord(id=self.KILL_SWITCH_ID, is_enabled=True, reason="Initialized")
            self.db.add(row)
            await self.db.flush()
        return row

    async def active_pause(self) -> AutomationPauseRecord | None:
        return (
            await self.db.execute(
                select(AutomationPauseRecord).where(AutomationPauseRecord.is_active.is_(True)).order_by(AutomationPauseRecord.created_at.desc())
            )
        ).scalar_one_or_none()

    async def open_automated_positions(self) -> int:
        result = await self.db.execute(
            select(func.count(PositionRecord.id)).where(PositionRecord.is_open.is_(True), PositionRecord.metadata_json["source"].as_string() == "automation")
        )
        return int(result.scalar() or 0)

    async def recent_health_is_safe(self) -> tuple[bool, str | None]:
        event = (
            await self.db.execute(
                select(ServiceHealthEvent).order_by(ServiceHealthEvent.observed_at.desc())
            )
        ).scalar_one_or_none()
        if event is None:
            return False, "No recent service health events available."
        if event.status != "healthy":
            return False, f"Recent service health is {event.status}."
        return True, None

    async def recent_automated_orders(self) -> int:
        result = await self.db.execute(
            select(func.count(OrderRecord.id)).where(
                OrderRecord.metadata_json["automation_source"].as_string() == "automation",
                OrderRecord.created_at >= func.datetime("now", f"-{self.settings.orders_window_minutes} minutes"),
            )
        )
        return int(result.scalar() or 0)
