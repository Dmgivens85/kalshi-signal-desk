from __future__ import annotations

from kalshi_signal_shared import ExternalEntityModel, ExternalEntityType, ExternalObservationModel, ExternalObservationType


def build_article_entity(
    *,
    source_slug: str,
    article_id: str,
    title: str,
    summary: str | None,
    url: str | None,
    tags: list[str] | None = None,
    raw_payload: dict[str, object] | None = None,
) -> ExternalEntityModel:
    return ExternalEntityModel(
        source_slug=source_slug,
        external_id=article_id,
        entity_type=ExternalEntityType.ARTICLE,
        title=title,
        description=summary,
        url=url,
        tags=tags or [],
        raw_payload=raw_payload or {},
    )


def build_article_observation(
    *,
    source_slug: str,
    article_id: str,
    title: str,
    summary: str | None,
    url: str | None,
    tags: list[str],
    entities: list[str],
    raw_text_available: bool,
    raw_payload: dict[str, object],
) -> ExternalObservationModel:
    return ExternalObservationModel(
        source_slug=source_slug,
        external_entity_id=article_id,
        observation_type=ExternalObservationType.NEWS_ARTICLE,
        title=title,
        summary=summary,
        url=url,
        tags=tags,
        entities=entities,
        raw_text_available=raw_text_available,
        raw_payload=raw_payload,
    )
