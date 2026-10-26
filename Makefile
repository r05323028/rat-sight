.PHONY: install install-js install-py db-up db-down migrate api web test test-js test-py test-e2e geospatial-smoke rodent-report-smoke lint typecheck format-check build validate openspec-gate openspec-archive import-districts import-stormwater import-rodent-reports data-bootstrap

PNPM ?= corepack pnpm

# CHANGE=<name> selects the OpenSpec change for the gate and archive targets.
# With no value the gate falls back to the single active change.
CHANGE ?=
PROFILE ?= full-local

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

import-districts:
	uv run --package ratsight-api python -m ratsight_api.importers.administrative_districts $(ARGS)

import-stormwater:
	uv run --package ratsight-api python -m ratsight_api.importers.stormwater_pipelines $(ARGS)

import-rodent-reports:
	uv run --package ratsight-api python -m ratsight_api.importers.rodent_reports $(ARGS)

# Suppressed 250 m counts only; never downloads citizen data. Reuse terms unverified.
import-citizen-reports:
	uv run --package ratsight-api python -m ratsight_api.importers.citizen_report_aggregates $(ARGS)

# Persistent pinned-reference profile in its own Compose project/volume.
# ARGS accepts: up (default) | status | down, plus --inspect-only, --synthetic,
# --citizen-reports, --purge.
data-bootstrap:
	PROFILE=$(PROFILE) bash scripts/data_bootstrap.sh $(ARGS)

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

# Real browser -> FastAPI -> PostGIS smoke; uses an isolated disposable stack.
geospatial-smoke:
	bash scripts/geospatial_smoke.sh

rodent-report-smoke:
	bash scripts/rodent_report_smoke.sh

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
	bash -n scripts/data_bootstrap.sh
	bash scripts/setup-pi-seats.sh --dry-run
	rig spec validate --json rig.yaml
	openspec schema validate evidence-driven
	uv run pytest scripts/tests -q
	docker compose -f infra/docker-compose.yml config --quiet

# Deterministic check used by the archive wrapper; not an OpenSpec hook.
openspec-gate:
	uv run python scripts/openspec_quality_gate.py $(CHANGE)

# Wrapper only; direct `openspec archive` bypasses the project quality gate.
openspec-archive:
	uv run python scripts/openspec_quality_gate.py $(CHANGE)
	openspec archive $(CHANGE)
