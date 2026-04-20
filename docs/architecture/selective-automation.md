# Selective Automation

Phase 7 adds optional selective automation to Kalshi Signal Desk without changing the product’s default posture: manual review remains the normal path.

## Core Principles

- automation is disabled by default globally
- automation is disabled by default per policy
- only whitelisted strategies, markets, or categories are eligible
- deterministic risk checks always run again at submission time
- ambiguity falls back to manual review

## Flow

1. The runner scans recent active signals.
2. A matching policy is required before automation is even considered.
3. The system builds a normal preview order first.
4. The policy engine decides whether to block, pause, disable, or allow automation.
5. In dry-run mode, the system records the would-be action without live submission.
6. In live mode, the system auto-approves and submits only if every guard passes.

## Persistence

- `automation_policies`
- `automation_runs`
- `automation_events`
- `automation_pauses`
- `automation_failures`

These tables make every automation decision replayable and inspectable.
