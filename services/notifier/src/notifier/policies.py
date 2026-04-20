from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from notifier.models import DeliveryPolicy, NotificationCandidate, QuietHoursRule


def in_quiet_hours(now: datetime, rule: QuietHoursRule) -> bool:
    if not rule.is_enabled:
        return False
    try:
        local_now = now.astimezone(ZoneInfo(rule.timezone_name))
    except ZoneInfoNotFoundError:
        local_now = now
    start = rule.quiet_start_hour
    end = rule.quiet_end_hour
    if start == end:
        return False
    hour = local_now.hour
    if start < end:
        return start <= hour < end
    return hour >= start or hour < end


def decide_delivery_policy(candidate: NotificationCandidate, quiet_rule: QuietHoursRule, now: datetime) -> DeliveryPolicy:
    classification = candidate.classification or "digest_only"
    if classification == "digest_only":
        return DeliveryPolicy(should_send=False, reason="digest_only", classification=classification)

    if classification == "daytime_alert" and not quiet_rule.allow_daytime_info:
        return DeliveryPolicy(should_send=False, reason="daytime_disabled", classification=classification)

    quiet = in_quiet_hours(now, quiet_rule)
    critical = classification in {"critical_opportunity", "critical_risk_warning"}

    if quiet and not (candidate.overnight_flag and critical and quiet_rule.allow_critical_overnight):
        return DeliveryPolicy(should_send=False, reason="quiet_hours", classification=classification)

    priority = 0
    use_emergency = False
    retry = None
    expire = None
    if critical:
        priority = 1
        if candidate.overnight_flag and (candidate.confidence_score or 0.0) >= 0.95:
            use_emergency = True
            priority = 2
            retry = 60
            expire = 1800
    elif classification == "daytime_alert":
        priority = 0
    else:
        return DeliveryPolicy(should_send=False, reason="no_alert", classification=classification)

    return DeliveryPolicy(
        should_send=True,
        reason="send",
        priority=priority,
        use_emergency=use_emergency,
        retry_seconds=retry,
        expire_seconds=expire,
        quiet_hours_bypass=quiet and critical,
        classification=classification,
    )
