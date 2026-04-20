from __future__ import annotations

from app.db.models import SignalRecord


def rank_actionable(signals: list[SignalRecord]) -> list[SignalRecord]:
    return sorted(
        signals,
        key=lambda item: (
            item.confidence_score or item.confidence,
            item.overnight_priority_score or 0.0,
            -(item.risk_penalty_score or 0.0),
        ),
        reverse=True,
    )


def rank_overnight(signals: list[SignalRecord]) -> list[SignalRecord]:
    return sorted(
        [item for item in signals if item.overnight_flag],
        key=lambda item: (item.overnight_priority_score or 0.0, item.confidence_score or item.confidence),
        reverse=True,
    )


def rank_risk(signals: list[SignalRecord]) -> list[SignalRecord]:
    return sorted(signals, key=lambda item: (item.risk_penalty_score or 0.0), reverse=True)


def rank_digest(signals: list[SignalRecord]) -> list[SignalRecord]:
    return sorted(
        [item for item in signals if item.alert_classification in {"digest_only", "daytime_alert"}],
        key=lambda item: (item.confidence_score or item.confidence, item.created_at),
        reverse=True,
    )
