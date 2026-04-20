from __future__ import annotations

from notifier.models import DeliveryResult, NotificationMessage
from .base import NotificationProvider


class FuturePushProvider(NotificationProvider):
    name = "pwa_push"

    async def send(self, notification: NotificationMessage) -> DeliveryResult:
        return DeliveryResult(
            status="sent",
            provider=self.name,
            provider_message="queued_for_future_provider",
            payload=notification.model_dump(mode="json"),
        )

    async def validate(self, notification: NotificationMessage) -> None:
        return None

    async def healthcheck(self) -> dict[str, object]:
        return {"provider": self.name, "status": "future"}
