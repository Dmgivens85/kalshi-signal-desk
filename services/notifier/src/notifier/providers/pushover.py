from __future__ import annotations

import logging

import httpx

from notifier.config import NotifierSettings
from notifier.models import DeliveryResult, NotificationMessage
from .base import NotificationProvider

logger = logging.getLogger(__name__)


class PushoverProvider(NotificationProvider):
    name = "pushover"

    def __init__(self, settings: NotifierSettings) -> None:
        self.settings = settings

    async def validate(self, notification: NotificationMessage) -> None:
        if not notification.token:
            raise ValueError("Pushover token is required.")
        if not notification.user:
            raise ValueError("Pushover user is required.")
        if not notification.message:
            raise ValueError("Pushover message is required.")
        if notification.priority == 2:
            if notification.retry is None or notification.expire is None:
                raise ValueError("Emergency priority requires retry and expire.")
            if notification.retry < 30:
                raise ValueError("Emergency retry must be at least 30 seconds.")
            if notification.expire > 10800:
                raise ValueError("Emergency expire must be <= 10800 seconds.")

    async def send(self, notification: NotificationMessage) -> DeliveryResult:
        await self.validate(notification)
        payload = {
            "token": notification.token,
            "user": notification.user,
            "message": notification.message,
            "title": notification.title,
            "device": notification.device,
            "url": notification.url,
            "url_title": notification.url_title,
            "priority": notification.priority,
            "sound": notification.sound,
            "retry": notification.retry,
            "expire": notification.expire,
        }
        payload = {key: value for key, value in payload.items() if value is not None}
        logger.info("pushover_send", extra={"priority": notification.priority, "url": notification.url})
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(self.settings.pushover_api_url, data=payload)
        response.raise_for_status()
        body = response.json()
        return DeliveryResult(
            status="sent",
            provider=self.name,
            provider_message=str(body.get("status", "sent")),
            receipt=body.get("receipt"),
            payload=body,
        )

    async def healthcheck(self) -> dict[str, object]:
        configured = bool(self.settings.pushover_app_token)
        return {"provider": self.name, "status": "healthy" if configured else "degraded", "configured": configured}

    async def cancel(self, receipt: str) -> dict[str, object]:
        return {"status": "not_implemented", "receipt": receipt}
