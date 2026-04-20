from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from signal_engine.config import SignalEngineSettings
from signal_engine.models import ComponentScores, NotificationCandidate, UnifiedSignalInput


@dataclass(slots=True)
class PolicyDecision:
    urgency_tier: str
    suggested_action: str
    size_bucket: str
    classification: str
    should_alert: bool
    overnight_flag: bool
    dedupe_key: str
    expires_at: datetime | None
    notification_candidate: NotificationCandidate | None


def _is_overnight(now: datetime, settings: SignalEngineSettings) -> bool:
    hour = now.hour
    return hour >= settings.overnight_start_hour or hour < settings.overnight_end_hour


def apply_signal_policy(
    signal_input: UnifiedSignalInput,
    scores: ComponentScores,
    settings: SignalEngineSettings,
    *,
    duplicate_found: bool,
    cooldown_active: bool,
    now: datetime | None = None,
) -> PolicyDecision:
    now = now or datetime.now(timezone.utc)
    overnight_flag = _is_overnight(now, settings)
    dedupe_key = f"{signal_input.market_ticker}:{'overnight' if overnight_flag else 'day'}:{round(scores.confidence_score, 2)}"

    directional_edge = signal_input.kalshi_features.short_term_momentum + signal_input.enrichment_features.consensus_delta
    if directional_edge > 0.05:
        suggested_action = "consider_yes"
        direction = "yes"
    elif directional_edge < -0.05:
        suggested_action = "consider_no"
        direction = "no"
    else:
        suggested_action = "watch"
        direction = "watch"

    size_bucket = "small"
    if scores.confidence_score >= 0.82 and scores.risk_penalty_score <= 0.18:
        size_bucket = "medium"
    if scores.confidence_score >= 0.9 and scores.risk_penalty_score <= 0.12:
        size_bucket = "large"

    urgency_tier = "digest"
    classification = "digest_only"
    should_alert = False

    overnight_gate = (
        scores.confidence_score >= settings.overnight_confidence_threshold
        and signal_input.kalshi_features.liquidity_depth_score >= settings.overnight_min_liquidity_score
        and signal_input.kalshi_features.spread_width <= settings.overnight_max_spread_width
        and scores.risk_penalty_score <= settings.overnight_risk_penalty_max
        and (
            signal_input.enrichment_features.source_count >= 1
            or scores.kalshi_support_score >= 0.9
        )
    )
    daytime_gate = scores.confidence_score >= settings.daytime_confidence_threshold and scores.risk_penalty_score <= 0.35

    if overnight_flag and overnight_gate and not duplicate_found and not cooldown_active:
        should_alert = True
        if scores.overnight_priority_score >= settings.critical_priority_threshold:
            urgency_tier = "critical"
            classification = "critical_opportunity" if direction != "watch" else "critical_risk_warning"
        elif scores.confidence_score >= settings.risk_warning_threshold:
            urgency_tier = "elevated"
            classification = "critical_risk_warning"
    elif daytime_gate and not duplicate_found and not cooldown_active:
        urgency_tier = "elevated" if scores.confidence_score >= 0.75 else "standard"
        classification = "daytime_alert"
        should_alert = True
    elif duplicate_found or cooldown_active or scores.confidence_score < 0.45:
        urgency_tier = "none"
        classification = "no_alert"

    expires_at = now + timedelta(hours=8 if overnight_flag else 4)
    notification_candidate = None
    if should_alert:
        notification_candidate = NotificationCandidate(
            title=f"{signal_input.market_ticker} {classification.replace('_', ' ')}",
            message=f"{signal_input.market_title}: {suggested_action} with confidence {scores.confidence_score:.0%}.",
            deep_link=f"/alerts/{signal_input.market_ticker.lower()}",
            urgency=urgency_tier,
            dedupe_key=dedupe_key,
            expiration_time=expires_at,
            overnight_flag=overnight_flag,
        )

    return PolicyDecision(
        urgency_tier=urgency_tier,
        suggested_action=suggested_action,
        size_bucket=size_bucket,
        classification=classification,
        should_alert=should_alert,
        overnight_flag=overnight_flag,
        dedupe_key=dedupe_key,
        expires_at=expires_at,
        notification_candidate=notification_candidate,
    )
