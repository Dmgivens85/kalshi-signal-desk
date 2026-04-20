from __future__ import annotations

from signal_engine.models import ComponentScores, ExplainabilityPayload, UnifiedSignalInput


def build_explainability(
    signal_input: UnifiedSignalInput,
    scores: ComponentScores,
    *,
    urgency_tier: str,
    suggested_action: str,
    size_bucket: str,
) -> ExplainabilityPayload:
    k = signal_input.kalshi_features
    e = signal_input.enrichment_features
    supporting: list[str] = []
    weakening: list[str] = []

    if abs(k.short_term_momentum) > 0.35:
        supporting.append(f"Short-term momentum is elevated at {k.short_term_momentum:.2f}.")
    if abs(k.orderbook_imbalance) > 0.2:
        supporting.append(f"Orderbook imbalance is notable at {k.orderbook_imbalance:.2f}.")
    if e.source_count >= 2:
        supporting.append(f"{e.source_count} external sources contribute to the signal.")
    if e.catalyst_presence:
        supporting.append("Recent external catalyst coverage is present.")

    if k.spread_width > 0.1:
        weakening.append(f"Spread width is wide at {k.spread_width:.2f}.")
    if k.liquidity_depth_score < 0.4:
        weakening.append("Liquidity depth is below the preferred threshold.")
    if e.disagreement_score > 0.45:
        weakening.append(f"External disagreement score is elevated at {e.disagreement_score:.2f}.")
    if scores.risk_penalty_score > 0.25:
        weakening.append(f"Risk penalty is elevated at {scores.risk_penalty_score:.2f}.")

    summary = (
        f"{signal_input.market_title} shows confidence {scores.confidence_score:.0%} with "
        f"Kalshi support {scores.kalshi_support_score:.0%} and external support {scores.external_support_score:.0%}."
    )
    return ExplainabilityPayload(
        summary=summary,
        top_supporting_factors=supporting[:3],
        top_weakening_factors=weakening[:3],
        source_count=e.source_count,
        confidence_score=scores.confidence_score,
        urgency_tier=urgency_tier,
        suggested_action=suggested_action,
        suggested_size_bucket=size_bucket,
        evidence_references=signal_input.evidence_refs,
    )
