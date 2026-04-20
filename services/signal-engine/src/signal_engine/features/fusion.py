from __future__ import annotations

from app.db.models import KalshiMarket

from signal_engine.models import EnrichmentFeatureSet, KalshiFeatureSet, UnifiedSignalInput


def build_unified_signal_input(
    market: KalshiMarket,
    kalshi_features: KalshiFeatureSet,
    enrichment_features: EnrichmentFeatureSet,
    *,
    evidence_refs: list[dict[str, object]],
) -> UnifiedSignalInput:
    market_price = ((market.last_price or market.yes_bid or market.yes_ask or 50) / 100.0)
    return UnifiedSignalInput(
        market_ticker=market.ticker,
        market_title=market.title,
        market_price=market_price,
        close_time=market.close_time,
        kalshi_features=kalshi_features,
        enrichment_features=enrichment_features,
        evidence_refs=evidence_refs,
    )
