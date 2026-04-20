from __future__ import annotations

from statistics import mean


def american_odds_to_probability(odds: int | float) -> float:
    value = float(odds)
    if value > 0:
        return round(100.0 / (value + 100.0), 6)
    return round(abs(value) / (abs(value) + 100.0), 6)


def consensus_probability(probabilities: list[float]) -> float:
    return round(mean(probabilities), 6) if probabilities else 0.0


def divergence_score(probabilities: list[float]) -> float:
    if len(probabilities) < 2:
        return 0.0
    spread = max(probabilities) - min(probabilities)
    return round(min(1.0, spread / 0.25), 6)
