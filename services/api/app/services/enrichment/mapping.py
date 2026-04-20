from __future__ import annotations

import re
from difflib import SequenceMatcher

from app.db.models import MappingOverrideRecord, MarketSnapshot
from app.services.enrichment.schemas import EnrichmentMapping, NormalizedEnrichment


def _tokenize(text: str | None) -> set[str]:
    if not text:
        return set()
    return {token for token in re.split(r"[^a-z0-9]+", text.lower()) if len(token) > 2}


def map_enrichment_to_market(
    enrichment_id: str,
    enrichment: NormalizedEnrichment,
    markets: list[MarketSnapshot],
    overrides: list[MappingOverrideRecord],
) -> EnrichmentMapping | None:
    for override in overrides:
        provider_match = override.provider == enrichment.provider.value
        record_match = override.provider_record_id and override.provider_record_id == enrichment.provider_record_id
        ref_match = override.market_ref and enrichment.market_ref and override.market_ref == enrichment.market_ref
        if provider_match and (record_match or ref_match):
            return EnrichmentMapping(
                enrichment_id=enrichment_id,
                market_ticker=override.target_market_ticker,
                confidence=min(1.0, 0.82 + override.confidence_boost),
                strategy="manual_override",
                explanation=override.note or "Manual override matched enrichment to Kalshi market.",
                manual_override=True,
            )

    if enrichment.market_ref:
        exact = next((market for market in markets if market.market_ticker == enrichment.market_ref), None)
        if exact:
            return EnrichmentMapping(
                enrichment_id=enrichment_id,
                market_ticker=exact.market_ticker,
                confidence=0.97,
                strategy="exact_market_ref",
                explanation="External market reference exactly matched Kalshi market ticker.",
            )

    enrichment_tokens = _tokenize(enrichment.title) | _tokenize(enrichment.summary) | _tokenize(enrichment.market_ref)
    best_market: MarketSnapshot | None = None
    best_score = 0.0

    for market in markets:
        market_tokens = _tokenize(market.market_ticker) | _tokenize(market.title) | _tokenize(market.event_ticker)
        overlap = len(enrichment_tokens & market_tokens) / max(1, len(enrichment_tokens | market_tokens))
        fuzzy = SequenceMatcher(None, enrichment.title.lower(), market.title.lower()).ratio()
        score = (overlap * 0.7) + (fuzzy * 0.3)
        if score > best_score:
            best_score = score
            best_market = market

    if best_market is None or best_score < 0.22:
        return None

    return EnrichmentMapping(
        enrichment_id=enrichment_id,
        market_ticker=best_market.market_ticker,
        confidence=min(0.9, max(0.25, best_score)),
        strategy="semantic_overlap",
        explanation=f"Matched by shared topic tokens and title similarity to '{best_market.title}'.",
    )
