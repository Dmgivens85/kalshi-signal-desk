from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from kalshi_signal_shared import ExternalEntityModel, ExternalObservationModel, ExternalSourceModel


class ExternalProviderAdapter(ABC):
    source: ExternalSourceModel

    @abstractmethod
    async def fetch_entities(self) -> list[ExternalEntityModel]:
        raise NotImplementedError

    @abstractmethod
    async def fetch_markets_or_questions(self) -> list[ExternalEntityModel]:
        raise NotImplementedError

    @abstractmethod
    async def fetch_observations(self, entities: Sequence[ExternalEntityModel]) -> list[ExternalObservationModel]:
        raise NotImplementedError

    @abstractmethod
    async def normalize(
        self,
        entities: Sequence[ExternalEntityModel],
        observations: Sequence[ExternalObservationModel],
    ) -> tuple[list[ExternalEntityModel], list[ExternalObservationModel]]:
        raise NotImplementedError

    @abstractmethod
    async def healthcheck(self) -> dict[str, object]:
        raise NotImplementedError
