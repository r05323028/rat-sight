# Design

## Existing boundaries

Reuse `infra/docker-compose.yml`, Alembic migrations, and the archive-only importers. Do not add an ETL framework, API contract, bulk browser fetch, or new schema for already supported layers.

## Runtime

Add a distinct Compose project name and persistent named volume for `full-local`. The bootstrap checks free loopback ports before startup, never enumerates or kills unrelated listeners, and records only child PIDs it starts. API/Web restart commands reuse the same volume. Teardown stops only the named project when explicitly requested; default bootstrap does not delete data.

## Bootstrap flow

1. `--inspect-only` validates profile, source paths, hashes, importer arguments, ownership, and expected inventory without writing.
2. Normal mode starts or reuses the project-scoped PostGIS service, applies migrations, and preflights both pinned sources with each importer’s inspect-only validation before any import writes. If either source is missing, mismatched, or invalid, bootstrap exits before importing either layer.
3. After both preflights pass, imports run in deterministic order with existing transactional/idempotent behavior. An unexpected post-preflight failure marks bootstrap failed and does not report a populated inventory; verification must exercise failure after the first import and confirm the owned environment can be discarded/recreated without touching shared data.
4. Existing importer conflict/idempotency behavior remains authoritative. A changed or missing source fails closed; no silent download or replacement occurs.
5. API/Web launch uses existing Make targets or explicit environment/ports and preserves bounded API queries.

## Source handling

Raw archives are supplied under an operator-selected path outside Git. The command may download only the two documented verified URLs after checking the exact pinned hash; a mismatch aborts before import. Downloaded files are never committed. Candidate layers remain assessment-only: stormwater Candidate B is the next supported reference-layer recommendation; Candidate A remains blocked on explicit CRS/axis confirmation; public trash bins, sanitary sewers, manholes, and complaint activity remain no-go until source identity, license, CRS/axis, identifiers, currentness, privacy, and scientific meaning are verified.

## Verification

Use disposable test copies for import validation, then a persistent project-scoped environment for restart/idempotency and browser checks. Verify exact district count, stormwater source-record count, repeated bootstrap no-op, API health after restart, bounded viewport behavior, provenance, and synthetic separation. Inventory reports database counts and source versions without claiming completeness beyond pinned records.
