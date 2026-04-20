SHELL := /bin/bash

.PHONY: install dev up down logs lint typecheck test

install:
	pnpm install

dev:
	docker compose -f infra/compose/local.yml up --build

up:
	docker compose -f infra/compose/local.yml up -d --build

down:
	docker compose -f infra/compose/local.yml down --remove-orphans

logs:
	docker compose -f infra/compose/local.yml logs -f

lint:
	pnpm lint

typecheck:
	pnpm typecheck

test:
	python -m pytest services/api/tests
