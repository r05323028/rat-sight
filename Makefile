.PHONY: install install-js install-py db-up db-down migrate api web test test-js test-py test-e2e lint typecheck format-check build validate

PNPM ?= corepack pnpm

install: install-js install-py

install-js:
	$(PNPM) install --frozen-lockfile

install-py:
	uv sync --all-packages --all-groups

db-up:
	docker compose -f infra/docker-compose.yml up -d

db-down:
	docker compose -f infra/docker-compose.yml down

migrate:
	uv run --package ratsight-api alembic -c services/api/alembic.ini upgrade head

api:
	uv run --package ratsight-api uvicorn ratsight_api.main:app --reload

web:
	$(PNPM) --filter @ratsight/web dev

test: test-js test-py

test-js:
	$(PNPM) --filter @ratsight/web test

test-py:
	uv run pytest

test-e2e:
	$(PNPM) --filter @ratsight/web e2e

lint:
	$(PNPM) --filter @ratsight/web lint
	uv run ruff check .

typecheck:
	$(PNPM) --filter @ratsight/web typecheck
	uv run basedpyright

format-check:
	$(PNPM) --filter @ratsight/web format:check
	uv run ruff format --check .

build:
	$(PNPM) --filter @ratsight/web build

validate:
	bash -n scripts/setup-pi-seats.sh
	bash scripts/setup-pi-seats.sh --dry-run
	rig spec validate --json rig.yaml
	openspec schema validate evidence-driven
	docker compose -f infra/docker-compose.yml config --quiet
