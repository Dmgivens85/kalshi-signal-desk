FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /workspace

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY packages/python-common/pyproject.toml packages/python-common/pyproject.toml
COPY packages/kalshi-client/pyproject.toml packages/kalshi-client/pyproject.toml
COPY services/api/pyproject.toml services/api/pyproject.toml

RUN pip install --upgrade pip && pip install -e packages/python-common -e packages/kalshi-client -e services/api

COPY . .

EXPOSE 8000
