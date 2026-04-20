# Kalshi Integration

Phase 2 establishes the Kalshi integration foundation for Kalshi Signal Desk.

## Scope

- signed authenticated REST access
- authenticated WebSocket handshake support
- typed market and stream models
- replay-friendly market persistence
- server-side-only secret handling
- execution interfaces scaffolded but disabled by default

## Shared Client Package

Location: `packages/shared-py/src/kalshi_client`

Modules:

- `config.py`: demo/prod endpoint resolution and runtime settings
- `auth.py`: explicit path normalization plus RSA-PSS SHA256 signing
- `models.py`: typed REST resources, stream payloads, and normalized internal events
- `rest.py`: async REST client with retries, timeouts, and error mapping
- `ws.py`: reconnecting WebSocket manager with stale-stream detection
- `errors.py`: integration-specific exception hierarchy

## Current Kalshi Contract

Implemented against the current official docs as of April 20, 2026:

- REST and WebSocket requests sign `timestamp + method + request_path`
- query strings are removed before signing
- WebSocket auth signs `GET + /trade-api/ws/v2`
- authenticated websocket sessions carry both public and private channels
- `orderbook_delta` streams are expected to begin with `orderbook_snapshot`

References:

- [API Keys](https://docs.kalshi.com/getting_started/api_keys)
- [Quick Start: WebSockets](https://docs.kalshi.com/getting_started/quick_start_websockets)
- [OpenAPI spec](https://docs.kalshi.com/openapi.yaml)
- [AsyncAPI spec](https://docs.kalshi.com/asyncapi.yaml)

## Safety Boundary

`place_order()` exists only as a typed scaffold and raises unless trading is explicitly enabled. Phase 2 does not expose real execution through the UI and does not enable autonomous trading.
