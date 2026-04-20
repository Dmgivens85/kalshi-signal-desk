# Smoke Tests

Kalshi Signal Desk smoke tests are designed to answer one fast question after deploy:

Is this version healthy enough to trust for staging or production traffic?

## Scope

The smoke suite is intentionally narrow and fast. It validates:

- web shell availability
- PWA manifest presence
- API liveness and readiness
- database and Redis connectivity
- migration visibility
- worker health endpoints
- Kalshi REST and websocket auth checks when enabled
- notification, automation, kill-switch, and execution-mode safety

It does not place orders and it does not perform full end-to-end business testing.

## Entry Points

Run the Python runner directly:

```bash
python3 -m scripts.smoke --env local --expected-mode paper
```

Or use the wrapper:

```bash
./infra/scripts/smoke-test.sh --env staging --expected-mode paper
```

## Important Safety Defaults

- local defaults to not requiring Kalshi connectivity
- staging should require Kalshi demo connectivity
- production should never tolerate unexpected `live` mode unless you explicitly pass `--allow-live`

## Output

Every subsystem prints:

- `PASS` or `FAIL`
- failure reason
- suggested next step

The summary also reports whether rollback is recommended.
