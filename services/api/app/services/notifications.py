from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from notifier.config import NotifierSettings
from notifier.delivery import NotificationDeliveryWorkflow
from notifier.health import notifier_health
from notifier.models import NotificationCandidate, NotificationMessage

from app.core.config import APISettings


def build_notifier_settings(settings: APISettings) -> NotifierSettings:
    return NotifierSettings(
        database_url=settings.database_url,
        redis_url=settings.redis_url,
        pushover_api_url=settings.pushover_api_url,
        pushover_app_token=settings.pushover_app_token,
        pushover_default_user_key=settings.pushover_default_user_key,
        execution_mode=settings.resolved_execution_mode,
        default_deep_link_base=settings.notification_deep_link_base,
        dedupe_ttl_seconds=settings.notification_dedupe_window_seconds,
        delivery_retry_attempts=settings.notification_delivery_retry_attempts,
        quiet_hours_start=settings.notification_quiet_hours_start,
        quiet_hours_end=settings.notification_quiet_hours_end,
        scheduler_interval_seconds=settings.notifier_scheduler_interval_seconds,
    )


class NotificationService:
    def __init__(self, settings: APISettings, db: AsyncSession) -> None:
        self.workflow = NotificationDeliveryWorkflow(build_notifier_settings(settings), db)

    async def dispatch_candidate(self, candidate: NotificationCandidate) -> dict[str, object]:
        try:
            return await self.workflow.dispatch_candidate(candidate)
        finally:
            await self.workflow.aclose()

    async def health(self, db: AsyncSession) -> dict[str, object]:
        return await notifier_health(db)


__all__ = ["NotificationCandidate", "NotificationMessage", "NotificationService", "build_notifier_settings"]
