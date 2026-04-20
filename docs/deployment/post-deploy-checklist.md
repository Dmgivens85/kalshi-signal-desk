# Post-Deploy Checklist

Use this checklist immediately after a staging or production deployment.

## Staging

1. Run the smoke tests.
2. Confirm `/api/paper/status` reports `paper`.
3. Confirm no staging secret points at production Kalshi credentials.
4. Confirm worker health checks are green.
5. Confirm a paper-mode notification path is healthy.
6. Confirm the iPhone PWA opens over HTTPS and Add to Home Screen works in Safari.

## Production

1. Run the smoke tests against the new deployment.
2. Confirm execution mode is still `disabled` or `paper` unless this rollout explicitly authorized live.
3. Confirm kill-switch visibility.
4. Confirm automation status is healthy and not silently enabled.
5. Confirm notifier health and deep-link base URL.
6. Confirm worker services remain internal-only.
7. If any critical smoke check fails, keep traffic on the previous version or roll back immediately.
