# Notifier Service

The notifier service is the Phase 5 delivery layer for Kalshi Signal Desk. It consumes structured notification candidates from the signal engine and turns only policy-approved items into user-facing alerts.

## Responsibilities

- receive notifier-ready payloads from persisted signals
- apply delivery policy before contacting a provider
- suppress duplicates within a configurable cooldown window
- respect quiet hours while still allowing overnight critical alerts
- deliver through Pushover first
- persist durable delivery, audit, and receipt records
- expose health and inspection data to the API

## Service Boundaries

- `services/signal-engine` decides whether a signal is alert-worthy and emits a candidate payload
- `services/notifier` decides whether that candidate should be delivered right now
- `services/notifier` never creates trades or execution instructions
- provider integrations are isolated under `services/notifier/src/notifier/providers`

## Core Flow

1. Read recent signals with `notification_candidate_payload`.
2. Build a typed `NotificationCandidate`.
3. Resolve quiet-hour and device preferences.
4. Apply policy classification and urgency rules.
5. Check dedupe state in Redis, with database fallback.
6. Send with the configured provider.
7. Persist delivery row, audit rows, and provider receipt metadata.

## Storage

- `notification_deliveries` stores the final delivery outcome and deep link.
- `notification_audit_logs` stores step-by-step lifecycle events.
- `notification_receipts` stores emergency-priority receipt identifiers for later tracking.
- `quiet_hour_policies` stores per-user quiet-hour rules.
- `user_device_targets` stores provider-specific routing targets such as Pushover device names.

## Future Extensions

- PWA push can be added as another provider without changing policy or delivery orchestration.
- Receipt polling and cancellation can be layered on top of the existing receipt records.
- A durable queue can replace the current DB polling loop without changing the candidate model.
