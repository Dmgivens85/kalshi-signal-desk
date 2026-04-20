# Execution Modes

Kalshi Signal Desk supports three explicit execution modes:

- `disabled`: no submission path is available
- `paper`: approval, automation, notifications, and reconciliation run normally, but order creation is simulated locally
- `live`: approved orders may be submitted to Kalshi, but only when live execution is explicitly enabled

## Safety Defaults

Development should default to `paper`. This keeps the platform connected to real Kalshi market data, the real signal engine, and the real notification pipeline while preventing accidental order submission.

Live execution requires multiple conditions to be true at the same time:

- `EXECUTION_MODE=live`
- `EXECUTION_LIVE_CONFIRMATION=true`
- `KALSHI_ENABLE_TRADING=true`
- the global kill switch is off
- deterministic risk checks pass
- the order has completed the required approval or automation guardrail path

If any one of those checks fails, the system falls back to a non-live path or blocks the action.

## Runtime Behavior

The active execution mode is resolved from configuration and can be overridden operationally through the paper-mode API controls. The API surfaces the current mode so the web app and notifier can label the experience clearly.

Mode semantics:

- `disabled` blocks both live and paper submission
- `paper` persists local paper orders, fills, positions, and portfolio snapshots
- `live` preserves the existing server-side Kalshi submission flow

## UI And Alert Labeling

To reduce operator confusion:

- the web app renders a mode banner on every page
- paper notifications are prefixed with `[PAPER]`
- paper orders, fills, and performance are stored separately from live execution records

## Why This Separation Matters

Paper mode is designed to preserve parity with the live workflow without sharing the final side effect. The same signal engine, notifier, approval flow, automation policy engine, and execution guardrails can be validated against real market movement before live deployment.
