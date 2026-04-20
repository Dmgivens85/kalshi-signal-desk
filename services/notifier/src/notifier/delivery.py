from __future__ import annotations

import logging
from datetime import datetime, timezone

from redis.asyncio import Redis
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.db.models import (
    NotificationAuditLogRecord,
    NotificationDeliveryRecord,
    NotificationEndpoint,
    QuietHourPolicyRecord,
    SignalRecord,
    UserDeviceTargetRecord,
)
from notifier.config import NotifierSettings
from notifier.dedupe import DedupeStore
from notifier.models import NotificationCandidate, NotificationMessage, QuietHoursRule, ReceiptTracking
from notifier.policies import decide_delivery_policy
from notifier.providers import FuturePushProvider, PushoverProvider
from notifier.receipts import record_receipt

logger = logging.getLogger(__name__)


class NotificationDeliveryWorkflow:
    def __init__(self, settings: NotifierSettings, db: AsyncSession) -> None:
        self.settings = settings
        self.db = db
        self.redis = Redis.from_url(settings.redis_url)
        self.dedupe = DedupeStore(self.redis)
        self.providers = {
            "pushover": PushoverProvider(settings),
            "pwa_push": FuturePushProvider(),
        }

    async def aclose(self) -> None:
        await self.redis.aclose()

    async def dispatch_candidate(self, candidate: NotificationCandidate) -> dict[str, object]:
        endpoints = list(
            (await self.db.execute(select(NotificationEndpoint).where(NotificationEndpoint.is_enabled.is_(True)))).scalars().all()
        )
        results: list[dict[str, object]] = []
        for endpoint in endpoints:
            results.append(await self._dispatch_to_endpoint(endpoint, candidate))
        await self.db.commit()
        return {"items": results}

    async def _dispatch_to_endpoint(self, endpoint: NotificationEndpoint, candidate: NotificationCandidate) -> dict[str, object]:
        quiet_rule = await self._quiet_rule(endpoint.user_id)
        if not endpoint.quiet_hours_enabled:
            quiet_rule.is_enabled = False
        policy = decide_delivery_policy(candidate, quiet_rule, datetime.now(timezone.utc))
        title = self._paper_label(f"{endpoint.title_prefix or ''}{candidate.title}")
        message_body = self._paper_label(candidate.message)
        delivery = NotificationDeliveryRecord(
            endpoint_id=endpoint.id,
            provider=endpoint.provider,
            dedupe_key=candidate.dedupe_key,
            title=title,
            message=message_body,
            deep_link_url=self._build_deep_link(endpoint, candidate.deep_link),
            priority=policy.priority,
            urgency=candidate.urgency,
            overnight_flag=candidate.overnight_flag,
            expires_at=candidate.expiration_time,
            signal_id=candidate.signal_id,
            payload={"candidate": candidate.model_dump(mode="json")},
        )
        self.db.add(delivery)
        await self.db.flush()

        await self._audit(delivery.id, candidate.signal_id, "candidate_received", "pending", candidate.model_dump(mode="json"))

        if not policy.should_send:
            delivery.status = "suppressed_quiet_hours" if policy.reason == "quiet_hours" else "suppressed_policy"
            delivery.quiet_hours_suppressed = policy.reason == "quiet_hours"
            await self._audit(delivery.id, candidate.signal_id, "suppressed", delivery.status, {"reason": policy.reason})
            return delivery.to_dict()

        duplicate = await self.dedupe.check_and_mark(self.db, candidate.dedupe_key, self.settings.dedupe_ttl_seconds)
        if duplicate:
            delivery.status = "suppressed_duplicate"
            delivery.dedupe_suppressed = True
            await self._audit(delivery.id, candidate.signal_id, "suppressed_duplicate", "suppressed_duplicate", {})
            return delivery.to_dict()

        device = endpoint.device_target or await self._primary_device(endpoint.user_id, endpoint.provider)
        message = NotificationMessage(
            token=self.settings.pushover_app_token,
            user=endpoint.destination or self.settings.pushover_default_user_key,
            message=message_body,
            title=title,
            device=device,
            url=self._build_deep_link(endpoint, candidate.deep_link),
            url_title="Open Signal Desk",
            priority=policy.priority,
            retry=policy.retry_seconds,
            expire=policy.expire_seconds,
            provider=endpoint.provider,
        )

        provider = self.providers.get(endpoint.provider)
        if provider is None:
            delivery.status = "failed"
            delivery.last_error = f"Unsupported provider: {endpoint.provider}"
            await self._audit(delivery.id, candidate.signal_id, "failed", "failed", {"error": delivery.last_error})
            return delivery.to_dict()
        try:
            async for attempt in AsyncRetrying(
                stop=stop_after_attempt(self.settings.delivery_retry_attempts),
                wait=wait_exponential(multiplier=0.5, min=0.5, max=4),
                retry=retry_if_exception_type(Exception),
                reraise=True,
            ):
                with attempt:
                    result = await provider.send(message)
            delivery.status = result.status
            delivery.provider_receipt = result.receipt
            delivery.attempt_count += 1
            delivery.payload = {"candidate": candidate.model_dump(mode="json"), "provider_result": result.payload}
            if result.receipt:
                await record_receipt(
                    self.db,
                    ReceiptTracking(
                        delivery_id=delivery.id,
                        receipt=result.receipt,
                        expires_at=candidate.expiration_time,
                        payload=result.payload,
                    ),
                )
            await self._audit(delivery.id, candidate.signal_id, "sent", result.status, result.payload)
        except Exception as exc:
            delivery.status = "failed"
            delivery.attempt_count += 1
            delivery.last_error = str(exc)
            await self._audit(delivery.id, candidate.signal_id, "failed", "failed", {"error": str(exc)})
        return delivery.to_dict()

    async def process_signal_queue(self) -> dict[str, object]:
        signals = list(
            (
                await self.db.execute(
                    select(SignalRecord)
                    .where(SignalRecord.notification_candidate_payload != {})
                    .order_by(desc(SignalRecord.created_at))
                    .limit(20)
                )
            ).scalars().all()
        )
        processed = 0
        for signal in signals:
            payload = signal.notification_candidate_payload or {}
            candidate = NotificationCandidate(
                signal_id=signal.id,
                market_ticker=signal.market_ticker,
                title=payload.get("title", signal.market_ticker),
                message=payload.get("message", signal.reason_summary or signal.thesis),
                deep_link=payload.get("deep_link", f"/signals/{signal.id}"),
                urgency=payload.get("urgency", signal.urgency_tier or "standard"),
                dedupe_key=payload.get("dedupe_key", signal.dedupe_key or signal.id),
                expiration_time=signal.expires_at,
                overnight_flag=signal.overnight_flag,
                classification=signal.alert_classification,
                confidence_score=signal.confidence_score or signal.confidence,
            )
            await self.dispatch_candidate(candidate)
            processed += 1
        return {"processed": processed}

    async def _quiet_rule(self, user_id: str | None) -> QuietHoursRule:
        if user_id:
            row = (
                await self.db.execute(
                    select(QuietHourPolicyRecord).where(QuietHourPolicyRecord.user_id == user_id).order_by(desc(QuietHourPolicyRecord.created_at))
                )
            ).scalar_one_or_none()
            if row is not None:
                return QuietHoursRule(
                    timezone_name=row.timezone_name,
                    quiet_start_hour=row.quiet_start_hour,
                    quiet_end_hour=row.quiet_end_hour,
                    allow_critical_overnight=row.allow_critical_overnight,
                    allow_daytime_info=row.allow_daytime_info,
                    is_enabled=row.is_enabled,
                )
        return QuietHoursRule(
            quiet_start_hour=self.settings.quiet_hours_start,
            quiet_end_hour=self.settings.quiet_hours_end,
        )

    async def _primary_device(self, user_id: str | None, provider: str) -> str | None:
        if not user_id:
            return None
        row = (
            await self.db.execute(
                select(UserDeviceTargetRecord)
                .where(
                    UserDeviceTargetRecord.user_id == user_id,
                    UserDeviceTargetRecord.provider == provider,
                    UserDeviceTargetRecord.is_enabled.is_(True),
                )
                .order_by(desc(UserDeviceTargetRecord.is_primary), desc(UserDeviceTargetRecord.created_at))
            )
        ).scalar_one_or_none()
        return row.device_name if row else None

    def _build_deep_link(self, endpoint: NotificationEndpoint, path: str) -> str:
        if path.startswith("http://") or path.startswith("https://"):
            return path
        base = endpoint.default_deep_link_base or self.settings.default_deep_link_base
        return f"{base.rstrip('/')}/{path.lstrip('/')}"

    def _paper_label(self, text: str) -> str:
        if self.settings.execution_mode == "paper":
            return f"[PAPER] {text}"
        return text

    async def _audit(self, delivery_id: str | None, signal_id: str | None, event_type: str, status: str, payload: dict[str, object]) -> None:
        self.db.add(
            NotificationAuditLogRecord(
                delivery_id=delivery_id,
                signal_id=signal_id,
                event_type=event_type,
                status=status,
                payload=payload,
            )
        )
