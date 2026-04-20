from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid5, NAMESPACE_URL

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import AuthContext
from app.db.models import (
    AlertEventRecord,
    AutomationEventRecord,
    AutomationFailureRecord,
    AutomationPauseRecord,
    AutomationPolicyRecord,
    AutomationRunRecord,
    SignalRecord,
    SystemControlRecord,
)
from execution_engine.automation.anomaly_detection import AutomationAnomalyDetector
from execution_engine.automation.config import AutomationSettings
from execution_engine.automation.guards import AutomationGuardSet
from execution_engine.automation.models import AutomationDecision, AutomationRunContext, AutomationStatusSnapshot
from execution_engine.automation.policies import AutomationPolicyEngine
from execution_engine.automation.selectors import AutomationSelector
from execution_engine.models import ApprovalStatus
from app.services.execution import GuardedExecutionService


class AutomationRunner:
    def __init__(self, settings: AutomationSettings, db: AsyncSession, execution: GuardedExecutionService) -> None:
        self.settings = settings
        self.db = db
        self.execution = execution
        self.selector = AutomationSelector(db)
        self.guards = AutomationGuardSet(settings, db)
        self.policy_engine = AutomationPolicyEngine(settings)
        self.anomalies = AutomationAnomalyDetector(settings, db)

    async def status(self) -> AutomationStatusSnapshot:
        global_control = await self.guards.ensure_global_control()
        pause = await self.guards.active_pause()
        events = list((await self.db.execute(select(AutomationEventRecord).order_by(desc(AutomationEventRecord.created_at)).limit(20))).scalars().all())
        failures = list((await self.db.execute(select(AutomationFailureRecord).order_by(desc(AutomationFailureRecord.created_at)).limit(20))).scalars().all())
        active_policy_count = len(await self.selector.active_policies())
        return AutomationStatusSnapshot(
            global_enabled=global_control.is_enabled,
            global_paused=pause is not None,
            global_dry_run=self.settings.dry_run_default,
            blocked_reason=pause.reason if pause else global_control.reason,
            active_policy_count=active_policy_count,
            recent_events=[item.to_dict() for item in events],
            recent_failures=[item.to_dict() for item in failures],
        )

    async def evaluate_pending_signals(self, limit: int = 10) -> dict[str, object]:
        anomaly = await self.anomalies.detect()
        if anomaly.triggered:
            await self._pause_due_to_anomaly(anomaly.reason or "anomaly", anomaly.detail or "Automation anomaly detected.", anomaly.payload)
        signals = list(
            (
                await self.db.execute(
                    select(SignalRecord)
                    .where(SignalRecord.status == "active")
                    .order_by(desc(SignalRecord.created_at))
                    .limit(limit)
                )
            ).scalars().all()
        )
        processed = 0
        for signal in signals:
            await self.evaluate_signal(signal)
            processed += 1
        return {"processed": processed, "anomaly_triggered": anomaly.triggered, "anomaly_reason": anomaly.reason}

    async def evaluate_signal(self, signal: SignalRecord) -> AutomationRunRecord:
        existing = (
            await self.db.execute(
                select(AutomationRunRecord).where(AutomationRunRecord.signal_id == signal.id).order_by(desc(AutomationRunRecord.created_at))
            )
        ).scalar_one_or_none()
        if existing and existing.status in ["submitted", "dry_run_submitted", "manual_review_required", "automation_blocked", "automation_paused"]:
            return existing

        strategy = await self.selector.strategy_for_signal(signal)
        policy = await self.selector.policy_for_signal(signal, strategy)
        global_control = await self.guards.ensure_global_control()
        pause = await self.guards.active_pause()
        kill_switch = await self.guards.ensure_kill_switch()
        health_safe, _ = await self.guards.recent_health_is_safe()
        anomaly = await self.anomalies.detect()
        open_auto = await self.guards.open_automated_positions()

        context = AutomationRunContext(
            signal_id=signal.id,
            strategy_id=signal.strategy_id,
            strategy_slug=strategy.slug if strategy else None,
            market_ticker=signal.market_ticker,
            confidence_score=signal.confidence_score or signal.confidence,
            overnight_flag=signal.overnight_flag,
            suggested_size_bucket=signal.suggested_position_size_bucket,
            category=(strategy.slug if strategy else signal.market_ticker.split("-")[0].lower()),
        )
        eligibility = self.policy_engine.decide(
            context=context,
            policy=policy,
            global_enabled=global_control.is_enabled,
            paused=pause is not None,
            kill_switch_enabled=kill_switch.is_enabled,
            health_safe=health_safe,
            anomaly_triggered=anomaly.triggered,
            open_automated_positions=open_auto,
        )
        run = AutomationRunRecord(
            signal_id=signal.id,
            strategy_id=signal.strategy_id,
            order_id=None,
            policy_id=policy.id if policy else None,
            mode="dry_run" if eligibility.dry_run else "live",
            status=eligibility.decision.value,
            confidence_score=context.confidence_score,
            decision_payload={"reasons": eligibility.reasons, "warnings": eligibility.warnings, "policy_id": eligibility.policy_id},
            anomaly_reason=anomaly.reason if anomaly.triggered else None,
        )
        self.db.add(run)
        await self.db.flush()
        await self._event(run.id, signal.id, "eligibility_decided", eligibility.decision.value, "Automation eligibility evaluated.", {"reasons": eligibility.reasons, "warnings": eligibility.warnings})

        if signal.recommended_action not in {"buy_yes", "buy_no"}:
            run.status = AutomationDecision.MANUAL_REVIEW_REQUIRED.value
            await self._event(run.id, signal.id, "manual_review", run.status, "Signal action is not auto-eligible.", {})
            await self.db.commit()
            return run

        order = await self.execution.create_preview_from_signal(signal.id, AuthContext(subject="automation", role="system"))
        run.order_id = order.id

        if eligibility.decision != AutomationDecision.AUTOMATION_ALLOWED:
            run.status = eligibility.decision.value
            await self._event(run.id, signal.id, "manual_fallback", run.status, "Automation fell back to manual review.", {"order_id": order.id})
            await self.db.commit()
            return run

        if order.approval_status != ApprovalStatus.PENDING_APPROVAL.value:
            run.status = AutomationDecision.MANUAL_REVIEW_REQUIRED.value
            await self._failure(run.id, policy.id if policy else None, "risk_recheck", "Preview did not remain eligible for approval.", {"order_id": order.id})
            await self.db.commit()
            return run

        order.client_order_id = self._deterministic_client_order_id(signal.id, policy.id if policy else "global", signal.market_ticker)
        order.metadata_json = {**(order.metadata_json or {}), "automation_source": "automation", "policy_id": policy.id if policy else None}

        if eligibility.dry_run:
            run.status = "dry_run_submitted"
            await self._event(run.id, signal.id, "dry_run", run.status, "Automation dry-run captured the order without live submission.", {"order_id": order.id, "client_order_id": order.client_order_id})
            await self.db.commit()
            return run

        try:
            await self.execution.approve_order(order.id, AuthContext(subject="automation", role="system"), notes="Auto-approved by whitelisted automation policy.")
            result = await self.execution.execute_order(order.id, AuthContext(subject="automation", role="system"))
            run.status = "submitted"
            run.kalshi_order_id = result["order"].get("kalshi_order_id")
            run.result_payload = result
            await self._event(run.id, signal.id, "submitted", run.status, "Order auto-submitted under strict guardrails.", result)
        except Exception as exc:
            run.status = AutomationDecision.MANUAL_REVIEW_REQUIRED.value
            await self._failure(run.id, policy.id if policy else None, "submission_failure", str(exc), {"order_id": order.id})
            await self._event(run.id, signal.id, "submission_failed", run.status, "Automation submission failed and fell back to manual review.", {"error": str(exc)})
        await self.db.commit()
        return run

    async def enable(self, actor_user_id: str | None) -> dict[str, object]:
        control = await self.guards.ensure_global_control()
        control.is_enabled = True
        control.reason = "Selective automation explicitly enabled."
        control.updated_by_user_id = actor_user_id
        await self._event(None, None, "automation_enabled", "enabled", "Selective automation enabled.", {"actor_user_id": actor_user_id})
        await self.db.commit()
        return control.to_dict()

    async def disable(self, actor_user_id: str | None, reason: str | None = None) -> dict[str, object]:
        control = await self.guards.ensure_global_control()
        control.is_enabled = False
        control.reason = reason or "Selective automation disabled."
        control.updated_by_user_id = actor_user_id
        await self._event(None, None, "automation_disabled", "disabled", control.reason, {"actor_user_id": actor_user_id})
        await self.db.commit()
        return control.to_dict()

    async def pause(self, actor_user_id: str | None, reason: str) -> dict[str, object]:
        current = await self.guards.active_pause()
        if current is not None:
            return current.to_dict()
        pause = AutomationPauseRecord(reason=reason, triggered_by="user", is_active=True, resumed_by_user_id=None)
        self.db.add(pause)
        await self._event(None, None, "automation_paused", "paused", reason, {"actor_user_id": actor_user_id})
        await self.db.commit()
        await self.db.refresh(pause)
        return pause.to_dict()

    async def resume(self, actor_user_id: str | None, reason: str | None = None) -> dict[str, object]:
        current = await self.guards.active_pause()
        if current is None:
            return {"status": "not_paused"}
        current.is_active = False
        current.resume_reason = reason
        current.resumed_at = datetime.now(timezone.utc)
        current.resumed_by_user_id = actor_user_id
        await self._event(None, None, "automation_resumed", "resumed", reason or "Automation resumed.", {"actor_user_id": actor_user_id})
        await self.db.commit()
        return current.to_dict()

    async def _pause_due_to_anomaly(self, reason: str, detail: str, payload: dict[str, object]) -> None:
        pause = await self.guards.active_pause()
        if pause is None:
            pause = AutomationPauseRecord(reason=detail, triggered_by="anomaly", is_active=True)
            self.db.add(pause)
        await self._event(None, None, "automation_anomaly", "critical", detail, payload)
        self.db.add(
            AlertEventRecord(
                signal_id=None,
                market_ticker="AUTOMATION",
                dedupe_key=f"automation-anomaly-{reason}",
                alert_type="automation_critical",
                urgency="critical",
                overnight_flag=True,
                delivery_status="candidate",
                payload={"reason": reason, "detail": detail, **payload},
            )
        )
        await self.db.commit()

    async def _event(self, run_id: str | None, signal_id: str | None, event_type: str, status: str, detail: str, payload: dict[str, object]) -> None:
        self.db.add(
            AutomationEventRecord(
                run_id=run_id,
                signal_id=signal_id,
                event_type=event_type,
                status=status,
                severity="critical" if status == "critical" else "info",
                detail=detail,
                payload=payload,
            )
        )
        await self.db.flush()

    async def _failure(self, run_id: str | None, policy_id: str | None, failure_type: str, detail: str, payload: dict[str, object]) -> None:
        self.db.add(
            AutomationFailureRecord(
                run_id=run_id,
                policy_id=policy_id,
                failure_type=failure_type,
                detail=detail,
                payload=payload,
            )
        )
        await self.db.flush()

    def _deterministic_client_order_id(self, signal_id: str, policy_id: str, market_ticker: str) -> str:
        return str(uuid5(NAMESPACE_URL, f"{signal_id}:{policy_id}:{market_ticker}"))
