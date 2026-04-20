from __future__ import annotations

import re
from difflib import SequenceMatcher

from kalshi_signal_shared import ExternalEntityModel, ExternalMappingModel

from app.db.models import ExternalMarketMappingRecord, KalshiMarket


def _tokenize(value: str | None) -> set[str]:
    if not value:
        return set()
    return {token for token in re.split(r"[^a-z0-9]+", value.lower()) if len(token) > 2}


class MappingEngine:
    def map_entity(
        self,
        entity: ExternalEntityModel,
        kalshi_markets: list[KalshiMarket],
        overrides: list[ExternalMarketMappingRecord],
    ) -> ExternalMappingModel | None:
        for override in overrides:
            if (
                override.external_entity_id == entity.external_id
                and override.manual_override
                and override.is_active
            ):
                return ExternalMappingModel(
                    external_entity_id=entity.external_id,
                    kalshi_market_ticker=override.kalshi_market_ticker,
                    confidence_score=max(override.confidence_score, 0.98),
                    strategy="manual_override",
                    source_notes=override.source_notes or "Manual override preserved.",
                    manual_override=True,
                    mismatch_reasons=override.mismatch_reasons or [],
                    ambiguity_score=override.ambiguity_score or 0.0,
                    feature_snapshot=override.feature_snapshot or {},
                )

        ref = entity.metadata.get("market_ref") if isinstance(entity.metadata, dict) else None
        if ref:
            for market in kalshi_markets:
                if market.ticker == ref:
                    return ExternalMappingModel(
                        external_entity_id=entity.external_id,
                        kalshi_market_ticker=market.ticker,
                        confidence_score=0.97,
                        strategy="explicit_market_ref",
                        source_notes="Provider supplied explicit market reference.",
                    )

        entity_tokens = _tokenize(entity.title) | _tokenize(entity.description) | _tokenize(str(ref) if ref else None)
        best_market: KalshiMarket | None = None
        best_score = 0.0
        second_best = 0.0
        best_reasons: list[str] = []

        for market in kalshi_markets:
            market_tokens = _tokenize(market.title) | _tokenize(market.event_ticker) | _tokenize(market.ticker)
            overlap = len(entity_tokens & market_tokens) / max(1, len(entity_tokens | market_tokens))
            fuzzy = SequenceMatcher(None, entity.title.lower(), market.title.lower()).ratio()
            score = (overlap * 0.65) + (fuzzy * 0.35)
            if score > best_score:
                second_best = best_score
                best_score = score
                best_market = market
                best_reasons = [
                    f"token_overlap={overlap:.2f}",
                    f"title_similarity={fuzzy:.2f}",
                ]
            elif score > second_best:
                second_best = score

        if best_market is None or best_score < 0.24:
            return None

        ambiguity = max(0.0, min(1.0, second_best / max(best_score, 0.01)))
        mismatch_reasons: list[str] = []
        if ambiguity > 0.8:
            mismatch_reasons.append("Multiple Kalshi markets scored similarly; review recommended.")
        if best_score < 0.4:
            mismatch_reasons.append("Low-confidence semantic overlap; avoid assuming equivalence.")

        return ExternalMappingModel(
            external_entity_id=entity.external_id,
            kalshi_market_ticker=best_market.ticker,
            confidence_score=min(0.9, max(0.25, best_score)),
            strategy="token_similarity",
            source_notes=f"Mapped via {'; '.join(best_reasons)}.",
            mismatch_reasons=mismatch_reasons,
            ambiguity_score=ambiguity,
        )
