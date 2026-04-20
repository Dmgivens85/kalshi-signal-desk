# Pushover Integration

Pushover is the primary mobile delivery provider in v1 because it provides dependable iPhone notifications without requiring a native app build.

## Supported Fields

- `token`
- `user`
- `message`
- `title`
- `device`
- `url`
- `url_title`
- `priority`
- `sound`
- `retry`
- `expire`

## Priority Mapping

- digest-only items are not sent
- daytime informational alerts use normal priority
- critical overnight alerts use high priority by default
- emergency priority is reserved for the narrowest overnight cases and requires retry/expire

## Delivery Notes

- requests are sent as HTTPS `POST` calls to the configured Pushover endpoint
- provider validation happens before delivery
- response payloads are persisted on the delivery record
- emergency receipts are stored in `notification_receipts`

## Environment Variables

- `PUSHOVER_API_URL`
- `PUSHOVER_APP_TOKEN`
- `PUSHOVER_DEFAULT_USER_KEY`
- `NOTIFICATION_DEEP_LINK_BASE`

## Operational Guidance

- prefer account-level user keys only for default routing
- use `user_device_targets` when you want per-device targeting
- keep emergency priority rare to avoid training yourself to ignore alerts
