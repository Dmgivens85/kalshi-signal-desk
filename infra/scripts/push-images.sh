#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${REGISTRY_PREFIX:-}" ]]; then
  echo "REGISTRY_PREFIX is required, for example 123456789012.dkr.ecr.us-east-1.amazonaws.com/"
  exit 1
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
IMAGE_TAG="${IMAGE_TAG:-$(git -C "$ROOT_DIR" rev-parse --short HEAD 2>/dev/null || echo dev)}"

for image in kalshi-web kalshi-api kalshi-worker; do
  docker push "${REGISTRY_PREFIX}${image}:${IMAGE_TAG}"
done
