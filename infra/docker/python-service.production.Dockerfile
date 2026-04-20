FROM python:3.11-slim-bookworm AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH=/opt/venv/bin:$PATH

WORKDIR /workspace

RUN python -m venv /opt/venv \
    && apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY packages/shared-py/pyproject.toml packages/shared-py/pyproject.toml
COPY packages/kalshi-client/pyproject.toml packages/kalshi-client/pyproject.toml
COPY services/market-stream/pyproject.toml services/market-stream/pyproject.toml
COPY services/external-enrichment/pyproject.toml services/external-enrichment/pyproject.toml
COPY services/signal-engine/pyproject.toml services/signal-engine/pyproject.toml
COPY services/execution-engine/pyproject.toml services/execution-engine/pyproject.toml
COPY services/notifier/pyproject.toml services/notifier/pyproject.toml
COPY services/scheduler/pyproject.toml services/scheduler/pyproject.toml
COPY . .

RUN pip install --upgrade pip \
    && pip install -e packages/shared-py \
    && pip install -e packages/kalshi-client \
    && pip install -e services/market-stream \
    && pip install -e services/external-enrichment \
    && pip install -e services/signal-engine \
    && pip install -e services/execution-engine \
    && pip install -e services/notifier \
    && pip install -e services/scheduler

FROM python:3.11-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH=/opt/venv/bin:$PATH \
    PYTHONPATH=/workspace/packages/shared-py/src:/workspace/services/api:/workspace/services/market-stream/src:/workspace/services/external-enrichment/src:/workspace/services/signal-engine/src:/workspace/services/execution-engine/src:/workspace/services/notifier/src:/workspace/services/scheduler/src \
    SERVICE_MODULE=scheduler.main \
    SERVICE_HEALTH_PORT=9090

WORKDIR /workspace

RUN addgroup --system app && adduser --system --ingroup app app \
    && apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/venv /opt/venv
COPY --chown=app:app . .

USER app

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import os,sys,urllib.request; port=os.environ.get('SERVICE_HEALTH_PORT','9090'); sys.exit(0 if urllib.request.urlopen(f'http://127.0.0.1:{port}/ready', timeout=3).status == 200 else 1)"

CMD ["sh", "-c", "python -m ${SERVICE_MODULE}"]
