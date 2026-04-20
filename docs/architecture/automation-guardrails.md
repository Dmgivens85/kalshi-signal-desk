# Automation Guardrails

The automation layer is intentionally stricter than the manual alert path.

## Guardrails

- global automation must be explicitly enabled
- each automation policy must be explicitly enabled
- user opt-in must be turned on for the policy
- market and category allowlists must match
- automation confidence thresholds are higher than manual thresholds
- overnight thresholds are stricter still
- size buckets are capped
- open automated position count is capped
- the global trading kill switch blocks automation immediately
- degraded or stale health falls back to manual review

## Dry Run First

Dry run is the default safe testing mode. It creates the same evaluation and audit trail as live automation but stops before Kalshi submission.

## Manual Fallback

When automation is not clearly safe, the system creates a normal preview order and leaves it in the manual queue rather than trying to push through.
