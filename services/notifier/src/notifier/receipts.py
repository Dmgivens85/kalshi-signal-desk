from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import NotificationReceiptRecord
from notifier.models import ReceiptTracking


async def record_receipt(db: AsyncSession, tracking: ReceiptTracking) -> NotificationReceiptRecord:
    receipt = NotificationReceiptRecord(
        delivery_id=tracking.delivery_id,
        provider=tracking.provider,
        receipt=tracking.receipt,
        expires_at=tracking.expires_at,
        payload=tracking.payload,
        last_checked_at=datetime.now(timezone.utc),
    )
    db.add(receipt)
    await db.flush()
    return receipt
