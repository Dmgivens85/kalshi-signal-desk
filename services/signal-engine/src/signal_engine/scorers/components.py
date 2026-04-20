from __future__ import annotations

from signal_engine.models import ComponentScores, UnifiedSignalInput


def score_signal_components(signal_input: UnifiedSignalInput) -> ComponentScores:
    k = signal_input.kalshi_features
    e = signal_input.enrichment_features

    kalshi_support = max(
        0.0,
        min(
            1.0,
            0.25
            + (abs(k.short_term_momentum) * 0.22)
            + (k.move_size * 1.8 * 0.14)
            + (abs(k.orderbook_imbalance) * 0.18)
            + (k.unusual_activity_score * 0.14)
            + (k.liquidity_depth_score * 0.07),
        ),
    )
    external_support = max(
        0.0,
        min(
            1.0,
            (e.external_support_score * 0.55)
            + (min(1.0, abs(e.consensus_delta) / 0.2) * 0.2)
            + ((1.0 - e.disagreement_score) * 0.15)
            + (e.recency_score * 0.1),
        ),
    )
    catalyst_score = max(0.0, min(1.0, (0.7 if e.catalyst_presence else 0.0) + (e.recency_score * 0.2)))
    risk_penalty = max(
        0.0,
        min(
            1.0,
            (k.spread_width * 1.7)
            + ((1.0 - k.liquidity_depth_score) * 0.25)
            + (k.volatility_proxy * 0.1)
            + (k.time_to_resolution_factor * 0.08),
        ),
    )
    confidence = max(
        0.0,
        min(
            1.0,
            (kalshi_support * 0.42)
            + (external_support * 0.31)
            + (catalyst_score * 0.12)
            - (risk_penalty * 0.2)
            + (k.liquidity_depth_score * 0.08)
            + ((1.0 - min(1.0, k.spread_width / 0.2)) * 0.07),
        ),
    )
    overnight_priority = max(
        0.0,
        min(
            1.0,
            (confidence * 0.5)
            + (kalshi_support * 0.18)
            + (external_support * 0.18)
            + (catalyst_score * 0.08)
            - (risk_penalty * 0.14),
        ),
    )
    return ComponentScores(
        kalshi_support_score=round(kalshi_support, 6),
        external_support_score=round(external_support, 6),
        catalyst_score=round(catalyst_score, 6),
        confidence_score=round(confidence, 6),
        risk_penalty_score=round(risk_penalty, 6),
        overnight_priority_score=round(overnight_priority, 6),
    )
