from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import AuthContext
from app.core.config import APISettings
from app.db.models import (
    ApprovalRequestRecord,
    ExecutionAuditRecord,
    OrderRecord,
    PaperOrderRecord,
    PaperPortfolioSnapshotRecord,
    PaperPositionRecord,
    PositionRecord,
    RiskEventRecord,
    RiskLimit,
    SimulationRunRecord,
    SystemControlRecord,
)
from execution_engine.config import ExecutionEngineSettings
from execution_engine.models import ApprovalStatus, ReconciliationUpdate, TradeCandidate
from execution_engine.orders import OrderService
from execution_engine.paper import PaperExecutionService, ReplayService
from execution_engine.previews import PreviewService
from execution_engine.risk import DeterministicRiskEngine
from execution_engine.paper.models import ReplayRequest
from kalshi_client import CreateOrderRequest, KalshiHttpClient


class ExecutionError(Exception):
    pass


class GuardedExecutionService:
    KILL_SWITCH_ID = "global_trading"

    def __init__(self, settings: APISettings, db: AsyncSession, kalshi: KalshiHttpClient) -> None:
        self.settings = settings
        self.db = db
        engine_settings = ExecutionEngineSettings(
            overnight_mode_enabled=True,
            max_exposure_per_market_cents=25_000,
            max_exposure_per_category_cents=75_000,
            max_daily_drawdown_cents=50_000,
            max_simultaneous_positions=8,
            max_spread_cents=12,
            min_liquidity=100,
            max_category_concentration=0.55,
            cooldown_after_loss_minutes=90,
            min_time_to_resolution_minutes=60,
            overnight_max_spread_cents=8,
            overnight_min_liquidity=250,
        )
        self.risk_engine = DeterministicRiskEngine(engine_settings, db)
        self.preview_service = PreviewService(db, self.risk_engine)
        self.order_service = OrderService(db, kalshi, self.preview_service)
        self.paper_service = PaperExecutionService(
            db,
            fill_mode=settings.paper_fill_mode,
            slippage_bps=settings.paper_slippage_bps,
            partial_fill_ratio=settings.paper_partial_fill_ratio,
            default_cash_cents=settings.paper_default_cash_cents,
        )
        self.replay_service = ReplayService(db, self.paper_service)

    async def _audit(
        self,
        *,
        order_id: str | None,
        actor_user_id: str | None,
        event_type: str,
        detail: str,
        payload: dict[str, object],
        status: str = "recorded",
    ) -> None:
        self.db.add(
            ExecutionAuditRecord(
                order_id=order_id,
                actor_user_id=actor_user_id,
                event_type=event_type,
                detail=detail,
                payload=payload,
                status=status,
            )
        )
        await self.db.flush()

    async def get_kill_switch(self) -> SystemControlRecord:
        return await self.risk_engine.ensure_kill_switch()

    async def get_execution_mode(self) -> dict[str, object]:
        control = (
            await self.db.execute(select(SystemControlRecord).where(SystemControlRecord.id == "execution_mode"))
        ).scalar_one_or_none()
        if control is None:
            control = SystemControlRecord(
                id="execution_mode",
                is_enabled=self.settings.resolved_execution_mode != "disabled",
                reason=self.settings.resolved_execution_mode,
            )
            self.db.add(control)
            await self.db.commit()
            await self.db.refresh(control)
        mode = control.reason or self.settings.resolved_execution_mode
        return {"mode": mode, "enabled": control.is_enabled}

    async def set_execution_mode(self, mode: str, actor_user_id: str | None) -> dict[str, object]:
        control = (
            await self.db.execute(select(SystemControlRecord).where(SystemControlRecord.id == "execution_mode"))
        ).scalar_one_or_none()
        if control is None:
            control = SystemControlRecord(id="execution_mode")
            self.db.add(control)
        control.is_enabled = mode != "disabled"
        control.reason = mode
        control.updated_by_user_id = actor_user_id
        await self._audit(
            order_id=None,
            actor_user_id=actor_user_id,
            event_type="execution_mode_updated",
            detail=f"Execution mode changed to {mode}.",
            payload={"mode": mode},
        )
        await self.db.commit()
        return {"mode": mode, "enabled": control.is_enabled}

    async def set_kill_switch(self, *, enabled: bool, reason: str | None, actor_user_id: str | None) -> dict[str, object]:
        control = await self.get_kill_switch()
        control.is_enabled = enabled
        control.reason = reason
        control.updated_by_user_id = actor_user_id
        await self._audit(
            order_id=None,
            actor_user_id=actor_user_id,
            event_type="kill_switch_updated",
            detail=f"Trading {'enabled' if enabled else 'disabled'}",
            payload={"enabled": enabled, "reason": reason},
        )
        await self.db.commit()
        await self.db.refresh(control)
        return control.to_dict()

    async def _default_risk_limit(self, user_id: str | None) -> RiskLimit:
        result = await self.db.execute(select(RiskLimit).where(RiskLimit.name == "default"))
        risk_limit = result.scalar_one_or_none()
        if risk_limit is None:
            risk_limit = RiskLimit(user_id=user_id, name="default")
            self.db.add(risk_limit)
            await self.db.commit()
            await self.db.refresh(risk_limit)
        return risk_limit

    async def preview_order(self, request: CreateOrderRequest, actor: AuthContext, *, signal_id: str | None = None, signal_summary: str | None = None, overnight_flag: bool = False, confidence_score: float | None = None) -> dict[str, object]:
        candidate = TradeCandidate(
            signal_id=signal_id,
            market_ticker=request.ticker,
            side=request.side.value if hasattr(request.side, "value") else str(request.side),
            action=request.action,
            count=request.count,
            yes_price=request.yes_price,
            no_price=request.no_price,
            order_type=request.type.value if hasattr(request.type, "value") else str(request.type),
            time_in_force=getattr(request, "time_in_force", None),
            post_only=bool(getattr(request, "post_only", False)),
            reduce_only=bool(getattr(request, "reduce_only", False)),
            signal_summary=signal_summary,
            overnight_flag=overnight_flag,
            confidence_score=confidence_score,
        )
        preview = await self.preview_service.preview(candidate)
        return preview.model_dump(mode="json")

    async def create_preview_record(
        self,
        request: CreateOrderRequest,
        actor: AuthContext,
        *,
        signal_id: str | None = None,
        signal_summary: str | None = None,
        overnight_flag: bool = False,
        confidence_score: float | None = None,
    ) -> OrderRecord:
        candidate = TradeCandidate(
            signal_id=signal_id,
            market_ticker=request.ticker,
            side=request.side.value if hasattr(request.side, "value") else str(request.side),
            action=request.action,
            count=request.count,
            yes_price=request.yes_price,
            no_price=request.no_price,
            order_type=request.type.value if hasattr(request.type, "value") else str(request.type),
            time_in_force=getattr(request, "time_in_force", None),
            post_only=bool(getattr(request, "post_only", False)),
            reduce_only=bool(getattr(request, "reduce_only", False)),
            signal_summary=signal_summary,
            overnight_flag=overnight_flag,
            confidence_score=confidence_score,
        )
        return await self.order_service.create_preview_order(actor.subject if actor.subject != "anonymous" else None, candidate)

    async def create_preview_from_signal(self, signal_id: str, actor: AuthContext) -> OrderRecord:
        candidate = await self.preview_service.build_candidate_from_signal(signal_id)
        return await self.order_service.create_preview_order(actor.subject if actor.subject != "anonymous" else None, candidate)

    async def approve_order(self, order_id: str, actor: AuthContext, notes: str | None = None) -> OrderRecord:
        order = await self.order_service.get_order(order_id)
        if order is None:
            raise ExecutionError("Order preview not found.")
        if order.approval_status != ApprovalStatus.PENDING_APPROVAL.value:
            raise ExecutionError("Order is not awaiting approval.")
        return await self.order_service.approve(order, actor.subject, notes)

    async def reject_order(self, order_id: str, actor: AuthContext, notes: str | None = None) -> OrderRecord:
        order = await self.order_service.get_order(order_id)
        if order is None:
            raise ExecutionError("Order preview not found.")
        if order.approval_status not in {ApprovalStatus.PENDING_APPROVAL.value, ApprovalStatus.BLOCKED.value}:
            raise ExecutionError("Order cannot be rejected from its current state.")
        return await self.order_service.reject(order, actor.subject, notes)

    async def execute_order(self, order_id: str, actor: AuthContext) -> dict[str, object]:
        control = await self.get_kill_switch()
        if not control.is_enabled:
            raise ExecutionError(f"Global kill switch is active: {control.reason or 'no reason provided'}")
        order = await self.order_service.get_order(order_id)
        if order is None:
            raise ExecutionError("Order preview not found.")
        execution_mode = (await self.get_execution_mode())["mode"]
        if execution_mode == "disabled":
            raise ExecutionError("Execution mode is disabled.")
        if execution_mode == "paper":
            return await self.paper_service.submit_order(order, actor.subject)
        try:
            return await self.order_service.submit(order, actor.subject, self.settings.live_trading_enabled)
        except ValueError as exc:
            raise ExecutionError(str(exc)) from exc

    async def reconcile_order(self, update: ReconciliationUpdate) -> OrderRecord | None:
        return await self.order_service.reconcile(update)

    async def list_orders(self) -> dict[str, object]:
        return {"items": [order.to_dict() for order in await self.order_service.list_orders()]}

    async def get_order(self, order_id: str) -> OrderRecord:
        order = await self.order_service.get_order(order_id)
        if order is None:
            raise ExecutionError("Order not found.")
        return order

    async def list_positions(self) -> dict[str, object]:
        positions = list((await self.db.execute(select(PositionRecord).order_by(PositionRecord.created_at.desc()))).scalars().all())
        return {"items": [position.to_dict() for position in positions]}

    async def list_pending_approvals(self) -> dict[str, object]:
        approvals = await self.order_service.list_pending_approvals()
        return {"items": [item.to_dict() for item in approvals]}

    async def risk_summary(self) -> dict[str, object]:
        summary = await self.risk_engine.summary()
        limit = await self._default_risk_limit(None)
        return {"limits": limit.to_dict(), "status": summary}

    async def list_risk_events(self) -> dict[str, object]:
        events = list((await self.db.execute(select(RiskEventRecord).order_by(desc(RiskEventRecord.created_at)))).scalars().all())
        return {"items": [event.to_dict() for event in events]}

    async def list_audit_logs(self) -> dict[str, object]:
        result = await self.db.execute(select(ExecutionAuditRecord).order_by(ExecutionAuditRecord.created_at.desc()))
        return {"items": [item.to_dict() for item in result.scalars().all()]}

    async def paper_status(self) -> dict[str, object]:
        mode = await self.get_execution_mode()
        performance = await self.paper_service.performance()
        latest_snapshot = (
            await self.db.execute(select(PaperPortfolioSnapshotRecord).order_by(PaperPortfolioSnapshotRecord.created_at.desc()))
        ).scalar_one_or_none()
        return {
            "mode": mode["mode"],
            "enabled": mode["enabled"],
            "paper_only": True,
            "performance": performance.model_dump(mode="json"),
            "latest_portfolio_snapshot": latest_snapshot.to_dict() if latest_snapshot else None,
        }

    async def list_paper_orders(self) -> dict[str, object]:
        return {"items": [item.to_dict() for item in await self.paper_service.list_orders()]}

    async def get_paper_order(self, paper_order_id: str) -> dict[str, object]:
        item = await self.paper_service.get_order(paper_order_id)
        if item is None:
            raise ExecutionError("Paper order not found.")
        return item.to_dict()

    async def list_paper_positions(self) -> dict[str, object]:
        return {"items": [item.to_dict() for item in await self.paper_service.list_positions()]}

    async def paper_performance(self) -> dict[str, object]:
        return (await self.paper_service.performance()).model_dump(mode="json")

    async def start_replay(self, request: ReplayRequest) -> dict[str, object]:
        return (await self.replay_service.start(request)).model_dump(mode="json")

    async def get_replay(self, run_id: str) -> dict[str, object]:
        run = await self.db.get(SimulationRunRecord, run_id)
        if run is None:
            raise ExecutionError("Simulation run not found.")
        return run.to_dict()

    async def list_simulation_runs(self) -> dict[str, object]:
        runs = list((await self.db.execute(select(SimulationRunRecord).order_by(SimulationRunRecord.created_at.desc()))).scalars().all())
        return {"items": [run.to_dict() for run in runs]}
