from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AutomationEventRecord, AutomationFailureRecord, AutomationRunRecord, ServiceHealthEvent
from execution_engine.automation.config import AutomationSettings
from execution_engine.automation.models import AutomationAnomaly


class AutomationAnomalyDetector:
    def __init__(self, settings: AutomationSettings, db: AsyncSession) -> None:
        self.settings = settings
        self.db = db

    async def detect(self) -> AutomationAnomaly:
        window_start = datetime.now(timezone.utc) - timedelta(minutes=self.settings.anomaly_window_minutes)
        failures = (
            await self.db.execute(
                select(func.count(AutomationFailureRecord.id)).where(AutomationFailureRecord.created_at >= window_start)
            )
        ).scalar_one()
        if failures and failures >= self.settings.anomaly_failure_threshold:
            return AutomationAnomaly(triggered=True, reason="repeated_failures", detail="Repeated automation failures exceeded the configured threshold.", payload={"failures": failures}, observed_at=datetime.now(timezone.utc))

        rate_limit_failures = (
            await self.db.execute(
                select(func.count(AutomationFailureRecord.id)).where(
                    AutomationFailureRecord.failure_type == "rate_limit",
                    AutomationFailureRecord.created_at >= window_start,
                )
            )
        ).scalar_one()
        if rate_limit_failures:
            return AutomationAnomaly(triggered=True, reason="rate_limit_pressure", detail="Automation detected recent rate-limit pressure.", payload={"rate_limit_failures": rate_limit_failures}, observed_at=datetime.now(timezone.utc))

        stale_health = (
            await self.db.execute(select(ServiceHealthEvent).order_by(desc(ServiceHealthEvent.observed_at)))
        ).scalar_one_or_none()
        if stale_health is not None and stale_health.status != "healthy":
            return AutomationAnomaly(triggered=True, reason="service_health", detail="Recent service health is unavailable or degraded.", payload=stale_health.payload if stale_health else {}, observed_at=datetime.now(timezone.utc))

        rejected = (
            await self.db.execute(
                select(func.count(AutomationFailureRecord.id)).where(
                    AutomationFailureRecord.failure_type == "order_rejected",
                    AutomationFailureRecord.created_at >= window_start,
                )
            )
        ).scalar_one()
        if rejected and rejected >= self.settings.anomaly_failure_threshold:
            return AutomationAnomaly(triggered=True, reason="rejection_rate", detail="Automated order rejection rate is above the configured threshold.", payload={"rejections": rejected}, observed_at=datetime.now(timezone.utc))

        mismatch = (
            await self.db.execute(
                select(AutomationEventRecord).where(
                    AutomationEventRecord.event_type == "reconciliation_mismatch",
                    AutomationEventRecord.created_at >= window_start,
                ).order_by(desc(AutomationEventRecord.created_at))
            )
        ).scalar_one_or_none()
        if mismatch is not None:
            return AutomationAnomaly(triggered=True, reason="reconciliation_mismatch", detail=mismatch.detail, payload=mismatch.payload, observed_at=mismatch.created_at)

        runs = (
            await self.db.execute(
                select(func.count(AutomationRunRecord.id)).where(
                    AutomationRunRecord.created_at >= window_start,
                    AutomationRunRecord.status.in_(["submitted", "dry_run_submitted"]),
                )
            )
        ).scalar_one()
        if runs and runs > self.settings.max_orders_per_window:
            return AutomationAnomaly(triggered=True, reason="too_many_orders", detail="Automation produced too many orders in a short interval.", payload={"runs": runs}, observed_at=datetime.now(timezone.utc))

        return AutomationAnomaly(triggered=False)
