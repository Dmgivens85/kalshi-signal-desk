from __future__ import annotations

from datetime import datetime, timezone
from statistics import mean, pstdev

from kalshi_signal_shared import (
    ExternalConsensusFeature,
    ExternalObservationModel,
    ExternalObservationType,
    NewsCatalystCandidate,
)


def build_consensus_feature(
    *,
    kalshi_market_ticker: str,
    kalshi_probability: float,
    observations: list[ExternalObservationModel],
) -> ExternalConsensusFeature:
    probabilities = [obs.probability_value for obs in observations if obs.probability_value is not None]
    source_count = len(probabilities)
    consensus = mean(probabilities) if probabilities else kalshi_probability
    delta = consensus - kalshi_probability
    disagreement = min(1.0, pstdev(probabilities) / 0.2) if len(probabilities) >= 2 else 0.0
    now = datetime.now(timezone.utc)
    recency = 0.0
    if observations:
        freshest = max((obs.observed_at for obs in observations), default=now)
        age_hours = max(0.0, (now - freshest).total_seconds() / 3600)
        recency = max(0.0, 1.0 - min(1.0, age_hours / 48.0))
    catalyst_presence = any(obs.observation_type == ExternalObservationType.NEWS_ARTICLE for obs in observations)
    external_support = max(0.0, min(1.0, 0.5 + delta + (recency * 0.1) - (disagreement * 0.15)))
    return ExternalConsensusFeature(
        kalshi_market_ticker=kalshi_market_ticker,
        external_support_score=round(external_support, 6),
        consensus_delta=round(delta, 6),
        disagreement_score=round(disagreement, 6),
        source_count=source_count,
        recency_score=round(recency, 6),
        catalyst_presence=catalyst_presence,
        feature_details={"consensus_probability": round(consensus, 6)},
    )


def build_catalyst_candidates(observations: list[ExternalObservationModel]) -> list[NewsCatalystCandidate]:
    candidates: list[NewsCatalystCandidate] = []
    for observation in observations:
        if observation.observation_type != ExternalObservationType.NEWS_ARTICLE:
            continue
        candidates.append(
            NewsCatalystCandidate(
                external_entity_id=observation.external_entity_id,
                article_id=observation.external_entity_id,
                title=observation.title or "News item",
                summary=observation.summary,
                published_at=observation.observed_at,
                url=observation.url,
                tags=observation.tags,
                entities=observation.entities,
                relevance_hints=observation.ai_metadata.get("relevance_hints", []),
            )
        )
    return candidates
