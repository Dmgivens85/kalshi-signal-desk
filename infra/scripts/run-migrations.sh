#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

export PYTHONPATH="${ROOT_DIR}/packages/shared-py/src:${ROOT_DIR}/services/api:${ROOT_DIR}/services/external-enrichment/src:${ROOT_DIR}/services/signal-engine/src:${ROOT_DIR}/services/notifier/src:${ROOT_DIR}/services/execution-engine/src"

cd "${ROOT_DIR}"
alembic -c services/api/alembic.ini upgrade head
