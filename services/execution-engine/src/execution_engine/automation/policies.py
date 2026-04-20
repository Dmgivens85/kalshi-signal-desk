from __future__ import annotations

from execution_engine.automation.config import AutomationSettings
from execution_engine.automation.models import AutomationDecision, AutomationEligibility, AutomationRunContext
from app.db.models import AutomationPolicyRecord


SIZE_ORDER = {"micro": 0, "small": 1, "medium": 2, "large": 3}


class AutomationPolicyEngine:
    def __init__(self, settings: AutomationSettings) -> None:
        self.settings = settings

    def decide(
        self,
        *,
        context: AutomationRunContext,
        policy: AutomationPolicyRecord | None,
        global_enabled: bool,
        paused: bool,
        kill_switch_enabled: bool,
        health_safe: bool,
        anomaly_triggered: bool,
        open_automated_positions: int,
    ) -> AutomationEligibility:
        reasons: list[str] = []
        warnings: list[str] = []
        if anomaly_triggered:
            return AutomationEligibility(
                decision=AutomationDecision.AUTOMATION_DISABLED_DUE_TO_ANOMALY,
                reasons=["Automation disabled due to anomaly detection."],
                anomaly_detected=True,
            )
        if not global_enabled:
            return AutomationEligibility(decision=AutomationDecision.MANUAL_REVIEW_REQUIRED, reasons=["Selective automation is globally disabled."], dry_run=self.settings.dry_run_default)
        if paused:
            return AutomationEligibility(decision=AutomationDecision.AUTOMATION_PAUSED, reasons=["Selective automation is currently paused."], dry_run=self.settings.dry_run_default)
        if not kill_switch_enabled:
            return AutomationEligibility(decision=AutomationDecision.AUTOMATION_BLOCKED, reasons=["Global trading kill switch is active."], dry_run=self.settings.dry_run_default)
        if not health_safe:
            return AutomationEligibility(decision=AutomationDecision.MANUAL_REVIEW_REQUIRED, reasons=["Recent system health is degraded or stale."], dry_run=self.settings.dry_run_default)
        if policy is None:
            return AutomationEligibility(decision=AutomationDecision.MANUAL_REVIEW_REQUIRED, reasons=["No whitelisted automation policy matched this signal."], dry_run=self.settings.dry_run_default)
        if not policy.is_enabled:
            return AutomationEligibility(decision=AutomationDecision.MANUAL_REVIEW_REQUIRED, reasons=["Matched automation policy is disabled."], policy_id=policy.id, dry_run=policy.dry_run)
        if not policy.user_opt_in_enabled:
            return AutomationEligibility(decision=AutomationDecision.MANUAL_REVIEW_REQUIRED, reasons=["User automation opt-in is not enabled for this policy."], policy_id=policy.id, dry_run=policy.dry_run)

        min_confidence = policy.overnight_min_confidence_score if context.overnight_flag else policy.min_confidence_score
        if context.confidence_score < min_confidence:
            reasons.append(f"Confidence {context.confidence_score:.2f} is below automation threshold {min_confidence:.2f}.")
        if policy.allowed_market_tickers and context.market_ticker not in policy.allowed_market_tickers:
            reasons.append("Market is outside the automation allowlist.")
        if policy.allowed_categories and (context.category or "general") not in policy.allowed_categories:
            reasons.append("Category is outside the automation allowlist.")
        if context.suggested_size_bucket and SIZE_ORDER.get(context.suggested_size_bucket, 99) > SIZE_ORDER.get(policy.max_size_bucket, 99):
            reasons.append(f"Suggested size bucket {context.suggested_size_bucket} exceeds automation limit {policy.max_size_bucket}.")
        if open_automated_positions >= policy.max_open_automated_positions:
            reasons.append("Open automated position cap has been reached.")

        if reasons:
            return AutomationEligibility(
                decision=AutomationDecision.MANUAL_REVIEW_REQUIRED,
                reasons=reasons,
                warnings=warnings,
                policy_id=policy.id,
                dry_run=policy.dry_run,
            )
        return AutomationEligibility(
            decision=AutomationDecision.AUTOMATION_ALLOWED,
            reasons=["Signal satisfied automation policy thresholds."],
            warnings=warnings,
            policy_id=policy.id,
            dry_run=policy.dry_run,
        )
