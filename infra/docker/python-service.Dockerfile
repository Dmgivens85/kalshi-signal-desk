FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/workspace/packages/shared-py/src:/workspace/services/api:/workspace/services/market-stream/src:/workspace/services/external-enrichment/src:/workspace/services/signal-engine/src:/workspace/services/execution-engine/src:/workspace/services/notifier/src:/workspace/services/scheduler/src

WORKDIR /workspace

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY packages/shared-py/pyproject.toml packages/shared-py/pyproject.toml
COPY packages/kalshi-client/pyproject.toml packages/kalshi-client/pyproject.toml
COPY services/market-stream/pyproject.toml services/market-stream/pyproject.toml
COPY services/external-enrichment/pyproject.toml services/external-enrichment/pyproject.toml
COPY services/signal-engine/pyproject.toml services/signal-engine/pyproject.toml
COPY services/execution-engine/pyproject.toml services/execution-engine/pyproject.toml
COPY services/notifier/pyproject.toml services/notifier/pyproject.toml
COPY services/scheduler/pyproject.toml services/scheduler/pyproject.toml

RUN pip install --upgrade pip

COPY . .
