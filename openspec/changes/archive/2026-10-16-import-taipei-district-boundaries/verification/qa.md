# Independent QA — import-taipei-district-boundaries

**Verdict: NOT CLEAR (BLOCKED on QA-001)**

- Qitem: `qitem-20261015162630-04a28d820d885fe3`
- Evaluator: `verification.qa@rat-team` (not an author of the implementation)
- Candidate: uncommitted feature diff on `main` at `b056e2e` (working tree), `openspec/changes/import-taipei-district-boundaries`
- Date: 2026-10-15
- Scope: independent, read-only. No implementation file was edited.

## User outcome checked

A real user can import the documented Taipei administrative boundary archive into
PostGIS and see it served as an honest EPSG:4326 GeoJSON administrative-reference
layer, visually distinct from rodent observation and simulated-movement data.

## Commands and results

Environment: macOS, Python 3.12 (uv), Node 26 (pnpm 10), Docker 29.7.2 available.
PostGIS image `ghcr.io/baosystems/postgis:17-3.5` pulled for the integration attempt.

| # | Command | Result |
|---|---------|--------|
| V1 | `uv run pytest -q` (no DB) | **80 passed, 1 skipped** (skipped = PostGIS integration test) |
| V2 | `uv run pytest -q` (with `administrative_districts` table created from ORM metadata) | **81 passed, 0 skipped** |
| V3 | `uv run ruff check .` | **All checks passed** |
| V4 | `uv run ruff format --check .` | **193 files already formatted** |
| V5 | `uv run basedpyright` | **0 errors, 0 warnings, 0 notes** |
| V6 | `corepack pnpm --filter @ratsight/web test` | **3 files / 13 tests passed** |
| V7 | `corepack pnpm --filter @ratsight/web lint` | **pass** |
| V8 | `corepack pnpm --filter @ratsight/web typecheck` | **pass** |
| V9 | `corepack pnpm --filter @ratsight/web build` | **pass** |
| V10 | `corepack pnpm --filter @ratsight/web e2e` | **3 passed** (Playwright/Chromium) |
| V11 | `make validate` | **pass** (setup dry-run 9/9, rig spec valid, OpenSpec schema valid, 23 script tests passed, compose config valid) |
| V12 | `openspec validate import-taipei-district-boundaries` | **valid**, 2 warnings (requirement text > 500 chars) |
| V13 | `make openspec-gate CHANGE=import-taipei-district-boundaries` | **BLOCKED** — `verification/gate.json` missing (task 8, lead-owned; expected at this stage) |
| V14 | `make db-up` then `make migrate` | **FAIL** — see QA-001 |
| V15 | `make format-check` | **FAIL** — see QA-002 |
| V16 | `python -m ratsight_api.importers.administrative_districts --help` / missing archive | **pass**; missing archive exits `2` with `error: archive not found` |

### Real-PostGIS smoke (QA-only, outside the repo)

Because QA-001 blocks the migration, the gated integration test is skipped in V1.
To exercise the importer/query code path independently, the table was created
directly from the ORM metadata (`AdministrativeDistrict.__table__.create(engine)`)
in the disposable local dev database, and `/tmp` scripts (now deleted) drove:

- insert one district → read back via `list_administrative_districts` →
  `data_state=available`, 1 feature, `geometry.type=Polygon`,
  `district_name=中正區`, `data_class=ADMINISTRATIVE_REFERENCE`,
  `classification=UNVERIFIED`, top-level `provenance.source_url` present.
- repeat the same batch → `{'inserted': 0, 'updated': 0, 'unchanged': 1}`; row count stays 1.
- same version + different archive hash → `ImportConflictError` ("different archive hash").
- same version + omitted identifier → `ImportConflictError` ("omits previously imported
  district identifiers ['B']"); row count stays 2 (no partial delete).

This is evidence that the application/importer logic is sound **when the table exists**;
it does not validate the migration.

## Findings

### QA-001 — BLOCKING — `make migrate` fails on a fresh PostGIS; the feature's table is never created

**Files:**
- `services/api/alembic/versions/0002_administrative_districts.py:33` (`Geometry(geometry_type="GEOMETRY", srid=4326)`) and `:65` (`op.create_index("idx_administrative_districts_geometry", …)`)
- `services/api/alembic/versions/0001_initial_schema.py:29` and `:35` (same pre-existing pattern)
- `services/api/src/ratsight_api/infrastructure/database/models.py:41,85` (same column definition)

**Root cause:** `geoalchemy2==0.20.0` (pinned in `uv.lock`) defaults
`Geometry(spatial_index=True)`. `op.create_table` therefore emits the GiST index
`idx_<table>_geometry` automatically, and the explicit `op.create_index(...)` in
the migration creates the same name a second time. PostgreSQL raises
`DuplicateTable: relation "…" already exists`.

**Reproduction (V14):**

```text
$ make db-up        # fresh volume, healthy
$ make migrate
sqlalchemy.exc.ProgrammingError: (psycopg.errors.DuplicateTable)
relation "idx_spatial_artifacts_geometry" already exists
[SQL: CREATE INDEX idx_spatial_artifacts_geometry ON spatial_artifacts USING gist (geometry)]
```

Offline SQL shows the duplication explicitly:

```text
$ uv run --package ratsight-api alembic -c services/api/alembic.ini upgrade head --sql | grep 'CREATE INDEX'
CREATE INDEX idx_spatial_artifacts_geometry ON spatial_artifacts USING gist (geometry);
CREATE INDEX idx_spatial_artifacts_geometry ON spatial_artifacts USING gist (geometry);
CREATE INDEX idx_administrative_districts_geometry ON administrative_districts USING gist (geometry);
CREATE INDEX idx_administrative_districts_geometry ON administrative_districts USING gist (geometry);
```

0002 also fails in isolation (stamp 0001, then upgrade):

```text
$ alembic stamp 0001_initial_schema
$ alembic upgrade head
sqlalchemy.exc.ProgrammingError: (psycopg.errors.DuplicateTable)
relation "idx_administrative_districts_geometry" already exists
```

**Impact:** The documented prerequisite `make migrate` in
`docs/infrastructure/administrative-boundaries-import.md` and `README.md` cannot
succeed; `administrative_districts` is never created; the importer cannot persist
and the API's available-data path cannot be reached. The PostGIS integration test
stays skipped in the default suite. QA-001 alone blocks acceptance.

**Actionable fix (author):** declare `spatial_index=False` on the geometry columns
in the migrations (and align `models.py`), keeping the single explicit
`op.create_index`, or drop the explicit `op.create_index` and rely on the
geoalchemy2 default. Apply the same fix to `0001` so the chain can run. Re-run
`make db-up && make migrate` and the previously skipped integration test.

### QA-002 — MAJOR — `make format-check` fails on three web files

**Command (V15):** `make format-check` → `prettier --check .` reports:

```text
[warn] src/components/dashboard.tsx
[warn] src/components/map-view.test.tsx
[warn] src/lib/api.test.ts
[warn] Code style issues found in 3 files.
```

**Impact:** The repository's own format check fails for this feature. `make lint`
(eslint/ruff) and `make typecheck` do not catch it, so CI/acceptance that runs
`format-check` breaks.

**Actionable fix (author):** `corepack pnpm --filter @ratsight/web exec prettier --write
src/components/dashboard.tsx src/components/map-view.test.tsx src/lib/api.test.ts`,
then re-run `make format-check`.

## Classification and provenance check

Independent inspection of source, tests, and the real-PostGIS smoke confirms:

- `data_class=ADMINISTRATIVE_REFERENCE` is a separate discriminator from the
  epistemic `Classification` literal; `ADMINISTRATIVE_REFERENCE` is not in
  `Classification`, and the stored value is `classification=UNVERIFIED`
  (`test_administrative_reference_is_not_an_epistemic_observation_class`).
- Persistence constraints require `data_class='ADMINISTRATIVE_REFERENCE'` and a
  valid classification; the model tests assert both (`test_model_defines_expected_columns_and_constraints`).
- The API response is a GeoJSON FeatureCollection with `data_state`,
  `data_class`, and one top-level version-1 `provenance`; feature properties carry
  identity/data-class/classification/schema-version/source references and do **not**
  duplicate the full provenance object. Confirmed by API tests and V2/real-PostGIS smoke.
- Empty storage returns HTTP 200 `data_state=empty` with no features; storage
  failure returns 503 and malformed persisted data returns 500 — never disguised
  as empty and never fallback geometry (`test_empty_storage_is_honest_200`,
  `test_storage_failure_is_503_not_empty`, `test_malformed_persisted_data_is_explicit_error`).
- The screenshot-facing UI labels the layer `UNVERIFIED`, states it is
  administrative reference (not rodent/infrastructure/simulated), and shows source
  URL/attribution/license/currentness; simulation controls remain separate and
  `SIMULATED` (`dashboard.tsx`, e2e `selects a district through the keyboard-accessible list`).
- No fabricated Taipei district count, rodent statistic, or accuracy metric was found.

## Not checked / residual risk

- The government archive was **not re-downloaded**; the recorded SHA-256, 12-record
  count, and EPSG:3826 claims in `docs/evidence/taipei-district-boundaries-2026-10-15.md`
  were not independently re-verified in this pass (the adversarial review claims it did).
- MapLibre polygon rendering with a live basemap was **not** visually verified. The
  e2e test mocks the style JSON and API responses and asserts control/toggle/selection
  state, not rendered boundary geometry.
- The endpoint was exercised via ASGI with fake sessions and via one direct
  application call against the ORM-created table; no live HTTP server run.
- Alembic autogenerate/ORM-vs-migration parity was not exercised.
- `verification/gate.json` and `verification/traceability.md` do not exist yet
  (task 8, lead-owned), so `make openspec-gate` is BLOCKED. This is not a QA defect.

## QA position

The feature logic, contracts, classification/provenance separation, and frontend
states are well-covered and passed the runnable checks. QA-001 must be fixed and
the migration path re-run before this change can be accepted; QA-002 should be
fixed in the same repair. Return to `build.minimal-gap`; after repair, the
previously skipped PostGIS integration test and `make format-check` are the
regression gates to re-run.

## QA rerun after repair (2026-10-15) — QA-001 and QA-002 RESOLVED

Re-verification of the repaired candidate (`qitem-20261015165000-5dc5fab8`), independent
of the author's summary:

| Check | Command | Result |
|-------|---------|--------|
| Offline DDL | `alembic -c services/api/alembic.ini upgrade head --sql \| grep 'CREATE INDEX'` | exactly **one** `idx_spatial_artifacts_geometry` and **one** `idx_administrative_districts_geometry` (was two each) |
| Fresh migration | drop the empty dev tables + `alembic_version`, then `make migrate` | **exit 0**; `Running upgrade -> 0001_initial_schema` and `-> 0002_administrative_districts`; no duplicate-index error |
| Migrated schema | `pg_indexes` / `pg_constraint` query | `alembic_version = 0002`; one GiST index per table; `uq_administrative_districts_key` + all four CHECK constraints present |
| Integration test | `uv run pytest services/api/tests/test_administrative_districts_import.py -v -k idempotent` | **PASSED** (previously skipped; runs live against PostGIS, rolls back) |
| Full Python | `uv run pytest -q` | **81 passed, 0 skipped** (was 80/1) |
| Static checks | `uv run ruff check .`, `make format-check`, `uv run basedpyright` | ruff clean; **Prettier clean** (QA-002 fixed); basedpyright 0/0/0 |
| Web | `pnpm --filter @ratsight/web test/lint/typecheck/build/e2e` | 13 tests, lint, typecheck, build, and 3 e2e all pass |

QA-001 and QA-002 are resolved. The repaired candidate is **QA CLEAR**.

Residual (unchanged from the first pass): government archive hash/count was not
re-downloaded; live-basemap polygon rendering was not visually verified (e2e mocks the
style and API); no live HTTP server run.
