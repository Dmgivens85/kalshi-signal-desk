FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /workspace

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY packages/python-common/pyproject.toml packages/python-common/pyproject.toml
COPY services/worker/pyproject.toml services/worker/pyproject.toml

RUN pip install --upgrade pip && pip install -e packages/python-common -e services/worker

COPY . .
