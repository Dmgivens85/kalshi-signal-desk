# Risk Engine

The Phase 6 risk engine is deterministic by design. AI can help interpret signals, but it never decides whether a trade passes risk.

## Rules Enforced

- max exposure per market
- max exposure per category
- max daily drawdown
- max simultaneous positions
- spread threshold
- liquidity floor
- concentration guidance
- cooldown after losses
- time-to-resolution minimum
- global kill switch
- tighter overnight spread and liquidity rules

## Outputs

Each preview returns:

- pass or fail
- blocking reasons
- warnings
- exposure impact
- size recommendation
- whether manual approval is still allowed
- whether overnight rules changed the evaluation

## Auditability

When a rule blocks or materially affects a trade, the result is stored on:

- `orders.preview_payload`
- `orders.risk_check_payload`
- `risk_events`
- `execution_audit_logs`

This allows later replay, operator review, and backtesting-friendly analysis.
