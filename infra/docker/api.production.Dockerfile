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
COPY services/api/pyproject.toml services/api/pyproject.toml
COPY . .

RUN pip install --upgrade pip \
    && pip install -e packages/shared-py -e packages/kalshi-client -e services/api

FROM python:3.11-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH=/opt/venv/bin:$PATH \
    PYTHONPATH=/workspace/packages/shared-py/src:/workspace/services/api:/workspace/services/external-enrichment/src:/workspace/services/signal-engine/src:/workspace/services/notifier/src:/workspace/services/execution-engine/src

WORKDIR /workspace

RUN addgroup --system app && adduser --system --ingroup app app \
    && apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/venv /opt/venv
COPY --chown=app:app . .

USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import sys,urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/api/health/ready', timeout=3).status == 200 else 1)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
