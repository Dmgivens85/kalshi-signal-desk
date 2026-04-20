from __future__ import annotations

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import NotificationAuditLogRecord, NotificationDeliveryRecord


async def notifier_health(db: AsyncSession) -> dict[str, object]:
    deliveries = list(
        (await db.execute(select(NotificationDeliveryRecord).order_by(desc(NotificationDeliveryRecord.created_at)).limit(10))).scalars().all()
    )
    audits = list(
        (await db.execute(select(NotificationAuditLogRecord).order_by(desc(NotificationAuditLogRecord.created_at)).limit(10))).scalars().all()
    )
    return {
        "status": "healthy",
        "recent_deliveries": [item.to_dict() for item in deliveries],
        "recent_audits": [item.to_dict() for item in audits],
    }
