from __future__ import annotations

from kalshi_signal_shared import ExternalEntityModel, ExternalEntityType


def build_forecast_entity(
    *,
    source_slug: str,
    external_id: str,
    title: str,
    description: str | None,
    resolution_criteria: str | None,
    probability: float | None,
    url: str | None,
    category: str | None = None,
    tags: list[str] | None = None,
    raw_payload: dict[str, object] | None = None,
) -> ExternalEntityModel:
    return ExternalEntityModel(
        source_slug=source_slug,
        external_id=external_id,
        entity_type=ExternalEntityType.QUESTION,
        title=title,
        description=description,
        resolution_criteria=resolution_criteria,
        current_probability=probability,
        url=url,
        category=category,
        tags=tags or [],
        raw_payload=raw_payload or {},
    )
