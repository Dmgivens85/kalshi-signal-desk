from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    ApprovalRequestRecord,
    ExecutionAuditRecord,
    OrderRecord,
    PositionRecord,
    RiskEventRecord,
)
from execution_engine.approvals import ApprovalWorkflow
from execution_engine.models import ApprovalStatus, ReconciliationUpdate, TradeCandidate
from execution_engine.previews import PreviewService
from kalshi_client import CreateOrderRequest, CreateOrderResponse, KalshiHttpClient


class OrderService:
    def __init__(self, db: AsyncSession, kalshi: KalshiHttpClient, preview_service: PreviewService) -> None:
        self.db = db
        self.kalshi = kalshi
        self.preview_service = preview_service
        self.workflow = ApprovalWorkflow()

    async def create_preview_order(self, user_id: str | None, candidate: TradeCandidate) -> OrderRecord:
        preview = await self.preview_service.preview(candidate)
        price = candidate.yes_price if candidate.yes_price is not None else candidate.no_price
        order = OrderRecord(
            user_id=user_id,
            signal_id=candidate.signal_id,
            market_ticker=candidate.market_ticker,
            client_order_id=str(uuid4()),
            side=candidate.side,
            action=candidate.action,
            order_type=candidate.order_type,
            count=candidate.count,
            price=price,
            yes_price=candidate.yes_price,
            no_price=candidate.no_price,
            time_in_force=candidate.time_in_force,
            post_only=candidate.post_only,
            reduce_only=candidate.reduce_only,
            status=preview.approval_status.value,
            approval_status=preview.approval_status.value,
            requires_manual_approval=True,
            preview_payload=preview.model_dump(mode="json"),
            risk_check_payload=preview.risk_evaluation.model_dump(mode="json"),
            raw_request=preview.candidate_order,
            category=candidate.category,
            theme=candidate.theme,
            size_bucket=preview.size_suggestion.value,
        )
        self.db.add(order)
        await self.db.flush()
        self.db.add(
            ApprovalRequestRecord(
                order_id=order.id,
                requested_by_user_id=user_id,
                status=preview.approval_status.value,
                notes="Created from deterministic preview.",
            )
        )
        self.db.add(
            ExecutionAuditRecord(
                order_id=order.id,
                actor_user_id=user_id,
                event_type="order_previewed",
                status=preview.approval_status.value,
                detail=preview.risk_evaluation_summary,
                payload=preview.model_dump(mode="json"),
            )
        )
        if not preview.risk_evaluation.passed:
            self.db.add(
                RiskEventRecord(
                    order_id=order.id,
                    market_ticker=order.market_ticker,
                    severity="high",
                    rule_name="preview_blocked",
                    status="blocked",
                    detail="Preview blocked by deterministic checks.",
                    payload=preview.risk_evaluation.model_dump(mode="json"),
                )
            )
        await self.db.commit()
        await self.db.refresh(order)
        return order

    async def approve(self, order: OrderRecord, actor_user_id: str | None, notes: str | None = None) -> OrderRecord:
        request = self.workflow.transition(order, ApprovalStatus.APPROVED, actor_user_id=actor_user_id, notes=notes)
        self.db.add(request)
        self.db.add(
            ExecutionAuditRecord(
                order_id=order.id,
                actor_user_id=actor_user_id,
                event_type="order_approved",
                status=order.approval_status,
                detail=notes or "Order manually approved.",
                payload={"approved_at": order.approved_at.isoformat() if order.approved_at else None},
            )
        )
        await self.db.commit()
        await self.db.refresh(order)
        return order

    async def reject(self, order: OrderRecord, actor_user_id: str | None, notes: str | None = None) -> OrderRecord:
        request = self.workflow.transition(order, ApprovalStatus.REJECTED, actor_user_id=actor_user_id, notes=notes)
        self.db.add(request)
        self.db.add(
            ExecutionAuditRecord(
                order_id=order.id,
                actor_user_id=actor_user_id,
                event_type="order_rejected",
                status=order.approval_status,
                detail=notes or "Order manually rejected.",
                payload={},
            )
        )
        await self.db.commit()
        await self.db.refresh(order)
        return order

    async def submit(self, order: OrderRecord, actor_user_id: str | None, trading_enabled: bool) -> dict[str, object]:
        if not trading_enabled:
            raise ValueError("Trading integration is disabled in this environment.")
        if order.approval_status != ApprovalStatus.APPROVED.value:
            raise ValueError("Order must be approved before submission.")

        request_model = CreateOrderRequest(
            ticker=order.market_ticker,
            action=order.action,
            side=order.side,
            count=order.count,
            yes_price=order.yes_price,
            no_price=order.no_price,
            client_order_id=order.client_order_id,
            type=order.order_type,
            time_in_force=order.time_in_force,
            post_only=order.post_only,
            reduce_only=order.reduce_only,
        )
        response = await self.kalshi.create_order(request_model)
        self.workflow.transition(order, ApprovalStatus.SUBMITTED, actor_user_id=actor_user_id)
        order.kalshi_order_id = response.order.order_id
        order.raw_response = response.model_dump(mode="json")
        self.db.add(
            ExecutionAuditRecord(
                order_id=order.id,
                actor_user_id=actor_user_id,
                event_type="order_submitted",
                status="submitted",
                detail="Order submitted to Kalshi from the server-side execution layer.",
                payload=response.model_dump(mode="json"),
            )
        )
        await self.db.commit()
        return {"order": order.to_dict(), "remote": response.model_dump(mode="json")}

    async def get_order(self, order_id: str) -> OrderRecord | None:
        return (await self.db.execute(select(OrderRecord).where(OrderRecord.id == order_id))).scalar_one_or_none()

    async def list_orders(self) -> list[OrderRecord]:
        return list((await self.db.execute(select(OrderRecord).order_by(OrderRecord.created_at.desc()))).scalars().all())

    async def list_pending_approvals(self) -> list[OrderRecord]:
        return list(
            (
                await self.db.execute(
                    select(OrderRecord).where(OrderRecord.approval_status == ApprovalStatus.PENDING_APPROVAL.value).order_by(OrderRecord.created_at.desc())
                )
            ).scalars().all()
        )

    async def reconcile(self, update: ReconciliationUpdate) -> OrderRecord | None:
        order = await self.get_order(update.order_id)
        if order is None:
            return None
        order.status = str(update.status)
        if update.kalshi_order_id:
            order.kalshi_order_id = update.kalshi_order_id
        if update.fill_count > 0:
            position = (
                await self.db.execute(select(PositionRecord).where(PositionRecord.market_ticker == order.market_ticker, PositionRecord.is_open.is_(True)))
            ).scalar_one_or_none()
            if position is None:
                position = PositionRecord(
                    user_id=order.user_id,
                    market_ticker=order.market_ticker,
                    category=order.category,
                    side=order.side,
                    contracts_count=0,
                    average_entry_price=0,
                    exposure_cents=0,
                )
                self.db.add(position)
                await self.db.flush()
            position.contracts_count += update.fill_count
            position.average_entry_price = update.fill_price or position.average_entry_price
            position.exposure_cents += (update.fill_price or 0) * update.fill_count
            order.position_id = position.id
        self.db.add(
            ExecutionAuditRecord(
                order_id=order.id,
                actor_user_id=None,
                event_type="order_reconciled",
                status=order.status,
                detail="Order reconciled from Kalshi update.",
                payload=update.model_dump(mode="json"),
            )
        )
        await self.db.commit()
        await self.db.refresh(order)
        return order
