from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ExecutionAuditRecord


class AuditService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_events(self) -> list[ExecutionAuditRecord]:
        return list((await self.db.execute(select(ExecutionAuditRecord).order_by(ExecutionAuditRecord.created_at.desc()))).scalars().all())
