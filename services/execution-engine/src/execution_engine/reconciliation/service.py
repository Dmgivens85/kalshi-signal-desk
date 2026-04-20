from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import FillRecord, PositionRecord
from execution_engine.models import ReconciliationUpdate


class ReconciliationService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def record_fill(self, update: ReconciliationUpdate, *, position_id: str | None = None, order_id: str | None = None) -> FillRecord:
        fill = FillRecord(
            order_id=order_id or update.order_id,
            position_id=position_id,
            kalshi_fill_id=f"fill-{update.order_id}-{int(datetime.now(timezone.utc).timestamp())}",
            market_ticker=update.raw_payload.get("market_ticker") or "",
            side=update.raw_payload.get("side"),
            price=update.fill_price or 0,
            count=update.fill_count,
            fee_cents=update.raw_payload.get("fee_cents", 0),
            filled_at=datetime.now(timezone.utc),
            raw_payload=update.raw_payload,
        )
        self.db.add(fill)
        await self.db.flush()
        return fill

    async def mark_position_closed(self, position: PositionRecord, *, realized_pnl_cents: int) -> PositionRecord:
        position.is_open = False
        position.closed_at = datetime.now(timezone.utc)
        position.realized_pnl_cents = realized_pnl_cents
        await self.db.flush()
        return position
