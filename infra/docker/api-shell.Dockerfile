FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/workspace/packages/shared-py/src:/workspace/services/api:/workspace/services/external-enrichment/src:/workspace/services/signal-engine/src:/workspace/services/notifier/src:/workspace/services/execution-engine/src

WORKDIR /workspace

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY services/api/pyproject.toml services/api/pyproject.toml
COPY packages/shared-py/pyproject.toml packages/shared-py/pyproject.toml
COPY packages/kalshi-client/pyproject.toml packages/kalshi-client/pyproject.toml

RUN pip install --upgrade pip && pip install -e packages/shared-py -e packages/kalshi-client -e services/api

COPY . .

EXPOSE 8000
