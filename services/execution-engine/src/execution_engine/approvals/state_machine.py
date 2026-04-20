from __future__ import annotations

from datetime import datetime, timezone

from app.db.models import ApprovalRequestRecord, OrderRecord
from execution_engine.models import ApprovalStatus


class ApprovalWorkflow:
    TERMINAL = {ApprovalStatus.REJECTED, ApprovalStatus.CANCELED, ApprovalStatus.EXPIRED, ApprovalStatus.FILLED}

    def transition(self, order: OrderRecord, target: ApprovalStatus, *, actor_user_id: str | None = None, notes: str | None = None) -> ApprovalRequestRecord:
        now = datetime.now(timezone.utc)
        current = ApprovalStatus(order.approval_status)
        allowed = {
            ApprovalStatus.PROPOSED: {ApprovalStatus.BLOCKED, ApprovalStatus.PENDING_APPROVAL},
            ApprovalStatus.BLOCKED: {ApprovalStatus.REJECTED},
            ApprovalStatus.PENDING_APPROVAL: {ApprovalStatus.APPROVED, ApprovalStatus.REJECTED, ApprovalStatus.EXPIRED},
            ApprovalStatus.APPROVED: {ApprovalStatus.SUBMITTED, ApprovalStatus.CANCELED},
            ApprovalStatus.SUBMITTED: {ApprovalStatus.PARTIALLY_FILLED, ApprovalStatus.FILLED, ApprovalStatus.CANCELED},
            ApprovalStatus.PARTIALLY_FILLED: {ApprovalStatus.FILLED, ApprovalStatus.CANCELED},
            ApprovalStatus.REJECTED: set(),
            ApprovalStatus.CANCELED: set(),
            ApprovalStatus.EXPIRED: set(),
            ApprovalStatus.FILLED: set(),
        }
        if target not in allowed[current]:
            raise ValueError(f"Invalid approval transition: {current.value} -> {target.value}")

        order.approval_status = target.value
        if target == ApprovalStatus.APPROVED:
            order.approved_by_user_id = actor_user_id
            order.approved_at = now
        if target == ApprovalStatus.SUBMITTED:
            order.submitted_at = now
        order.status = target.value
        return ApprovalRequestRecord(
            order_id=order.id,
            requested_by_user_id=order.user_id,
            decided_by_user_id=actor_user_id,
            status=target.value,
            notes=notes,
            decided_at=now if actor_user_id else None,
        )
