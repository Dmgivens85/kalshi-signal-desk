from __future__ import annotations

from abc import ABC, abstractmethod

from notifier.models import DeliveryResult, NotificationMessage


class NotificationProvider(ABC):
    name: str

    @abstractmethod
    async def send(self, notification: NotificationMessage) -> DeliveryResult:
        raise NotImplementedError

    @abstractmethod
    async def validate(self, notification: NotificationMessage) -> None:
        raise NotImplementedError

    @abstractmethod
    async def healthcheck(self) -> dict[str, object]:
        raise NotImplementedError

    async def cancel(self, receipt: str) -> dict[str, object]:
        return {"status": "unsupported", "receipt": receipt}
