#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
IMAGE_TAG="${IMAGE_TAG:-$(git -C "$ROOT_DIR" rev-parse --short HEAD 2>/dev/null || echo dev)}"
REGISTRY_PREFIX="${REGISTRY_PREFIX:-}"

build_image() {
  local name="$1"
  local dockerfile="$2"
  local image_ref="${REGISTRY_PREFIX}${name}:${IMAGE_TAG}"
  echo "Building ${image_ref} using ${dockerfile}"
  docker build -f "${ROOT_DIR}/${dockerfile}" -t "${image_ref}" "${ROOT_DIR}"
}

build_image "kalshi-web" "infra/docker/web.production.Dockerfile"
build_image "kalshi-api" "infra/docker/api.production.Dockerfile"
build_image "kalshi-worker" "infra/docker/python-service.production.Dockerfile"

echo "Built images with tag ${IMAGE_TAG}"
