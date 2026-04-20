# Market Stream Service

Location: `services/market-stream`

## Responsibilities

- load a configured Kalshi watchlist
- bootstrap market metadata and current orderbooks from REST
- connect to Kalshi WebSockets with authenticated headers
- subscribe to `ticker` and `orderbook_delta`
- normalize raw websocket envelopes into internal market events
- persist market metadata, snapshots, orderbook deltas, and service heartbeats
- optionally cache latest state in Redis

## Persistence Layout

- `kalshi_markets`: canonical market metadata and current coarse state
- `market_snapshots`: append-only ticker and orderbook snapshots
- `orderbook_events`: replayable deltas and snapshot payloads
- `service_health_events`: worker lifecycle and heartbeat history

## Reliability

- exponential reconnects
- subscription replay after reconnect
- stale-stream timeout detection
- Redis latest-state cache separated from historical storage
- structured logging around connection lifecycle
