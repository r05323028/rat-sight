# Independent QA — add-geospatial-data-layers

**Verdict: CLEAR (feature scope)** — all specified QA checks pass independently.

- Qitem: `qitem-20261015192926-8049f83370cdb838`
- Evaluator: `verification.qa@rat-team` (not an author of the implementation)
- Candidate: uncommitted change `openspec/changes/add-geospatial-data-layers` on `main` at `af975c4`
- Date: 2026-10-15
- Scope: independent, read-only. No implementation file was edited.

## User outcome checked

A user can run a real browser → Next.js → FastAPI → PostGIS path for the Taipei
administrative-boundary layer, without the browser mock replacing the API, and see
the available and empty administrative states with provenance, while the synthetic
simulation stays independent.

## Commands and results

Environment: macOS, Python 3.12 (uv), Node 26 (pnpm), Docker 29.7.2 with
`ghcr.io/baosystems/postgis:17-3.5`.

| # | Command | Result |
|---|---------|--------|
| V1 | `openspec validate add-geospatial-data-layers` | **valid** |
| V2 | `uv run pytest -q` | **81 passed** |
| V3 | `corepack pnpm --filter @ratsight/web e2e` (default) | **3 passed, 2 skipped** — the two real-API specs skip without `PLAYWRIGHT_EXTERNAL_SERVERS` |
| V4 | `make geospatial-smoke` | **real-api.spec.ts 1 passed; real-api-empty.spec.ts 1 passed** |
| V5 | `make validate` | **pass** (rig spec valid, OpenSpec schema valid, 23 script tests, compose config valid, setup dry-run 9/9) |
| V6 | `uv run basedpyright` | **0 errors, 0 warnings, 0 notes** |
| V7 | `corepack pnpm --filter @ratsight/web lint` / `typecheck` | **pass** |

### Smoke detail and cleanup (V4)

- The initial V4 run used fixed project `ratsight-geospatial-smoke`, DB port `55439`,
  API `8000`, and web `3002`, with a temporary compose override and disposable volume.
  Corrective follow-up below replaced the fixed project with a per-invocation name.
- `alembic upgrade head` applied `0001` and `0002`; `scripts/seed_geospatial_smoke.py`
  seeded one explicitly synthetic fixture (`dataset_id=smoke-fixture`,
  `source_url=https://example.invalid/...`, attribution `RatSight automated test fixture`).
- Post-run state: **no listeners on 3002, 8000, or 55439**; **no smoke containers or
  volumes left**; the pre-existing dev `infra-postgres-1` container/volume was untouched.

## Independent checks of the acceptance criteria

- **Source registry (spec Requirement 1):** `docs/infrastructure/data-sources.md` now
  has a verified entry with Evidence ID `EVID-TPE-DISTRICT-BOUNDARIES-2026-10-15`,
  publisher, dataset/resource version `2022-09-15`, metadata/catalog/download URLs,
  SHP + `EPSG:3826`→`EPSG:4326`, coverage, archive SHA-256
  `77bcc347…d2d9` (matches the evidence file), license, and explicit post-2022
  `UNVERIFIED` currentness. Other sources remain candidates.
- **No API interception (spec Requirement 2):** both real-API specs only route
  `**/gl/positron-gl-style/style.json` (basemap) and assert the live response;
  `/api/v1/administrative-districts` is fetched from the running FastAPI app, not
  mocked. `playwright.config.ts` has no `webServer` when
  `PLAYWRIGHT_EXTERNAL_SERVERS` is set.
- **Populated path:** `real-api.spec.ts` asserts `data_state=available`,
  `data_class=ADMINISTRATIVE_REFERENCE`, `provenance.schema_version=1`,
  `classification=UNVERIFIED`, `geometry.type=Polygon`, district identity, and visible
  provenance in the dashboard.
- **Empty path:** `real-api-empty.spec.ts` asserts `data_state=empty`, `features=[]`,
  "No boundaries imported", and a disabled layer toggle — no fabricated geometry.
- **Fixture honesty:** the seed is marked synthetic and uses `ADMINISTRATIVE_REFERENCE`
  / `UNVERIFIED`; it calls the production `_build_batch`, `build_provenance`, and
  `persist_import` rather than reimplementing persistence.
- **Unavailable dependency:** the script exits `3` with
  `UNVERIFIED/NOT RUN: geospatial smoke unavailable …` when Docker is unavailable and
  also fails closed when a fixed port is occupied (source inspection).
- **Default e2e isolation:** the two external specs skip by default, so the hermetic
  suite still runs without FastAPI (V3).

## Findings

### QA-GDL-001 — INFO — repo-hygiene: untracked `.agents/skills/sem/**` breaks `make lint` and `make format-check` (not caused by this change)

**Command:** `uv run ruff check .` → **13 errors (E501)**, all in
`.agents/skills/sem/guard/sem-guard.py` (5), `.agents/skills/sem/badge/sem-live.py` (5),
`.agents/skills/sem/badge/statusline-sem.py` (2),
`.agents/skills/sem/badge/sem-activity.py` (1). `ruff format --check .` reports **4 files
would be reformatted**, all under `.agents/skills/sem/`.

`.agents/` and `skills-lock.json` are untracked, are not referenced by this change's
proposal/tasks/design, and appear to be a third-party `sem` skill installed into the
working tree (`skills-lock.json` records source `Ataraxy-Labs/sem`). They are not
excluded by `.gitignore` or the `[tool.ruff]` config, so the repository-wide lint/format
commands now fail. The feature's own new Python (`scripts/seed_geospatial_smoke.py`)
is clean.

**Actionable decision (lead/owner):** either add `.agents/` and `skills-lock.json` to
`.gitignore`, or add an explicit `exclude = [".agents"]` to `[tool.ruff]`, or instruct
the skill installer to place it outside the work tree. This is outside the
`add-geospatial-data-layers` delivery boundary and was not treated as a feature blocker.

## Not checked / residual risk

- The official government archive was **not re-downloaded**; the registry's hash and
  12-district claims were cross-checked against the repository evidence file only.
- The smoke still mocks the external basemap style (deliberately, for determinism); it
  does **not** verify Google/CARTO basemap availability or visual tile rendering.
- The smoke uses fixed ports and is local-only; it is not a hosted/CI-remote integration.
- Live HTTP correctness was exercised for the administrative endpoint and dashboard
  only; other endpoints are covered by hermetic tests.

## QA position

All specified checks passed during the independent evaluation; its result predates the corrective edits below. The unrelated `.agents/` lint/format hygiene issue remains outside feature scope.

## Corrective implementation follow-up

This follow-up was run after the independent QA above; results below are implementer-run, with a separate three-role read-only council review. No live data was ingested.

| Check | Result |
|-------|--------|
| `env POSTGRES_DB=wrong POSTGRES_USER=wrong POSTGRES_PASSWORD=wrong POSTGRES_PORT=54320 make geospatial-smoke` | **Pass** — migrations and both real FastAPI/PostGIS/Next specs passed despite conflicting inherited DB settings; run used Compose project `ratsight-geospatial-smoke-42484`. |
| Post-smoke container/volume and listener assertion | **Pass** — no matching smoke containers or volumes; no listeners on 55439, 8000, or 3002. |
| `bash -n scripts/geospatial_smoke.sh && uv run ruff check scripts/seed_geospatial_smoke.py && git diff --check` | **Pass** — shell syntax, fixture lint, and diff checks clean. |
| `corepack pnpm --filter @ratsight/web format:check && corepack pnpm --filter @ratsight/web typecheck && corepack pnpm --filter @ratsight/web test` | **Pass** — formatting/typecheck clean; 13 tests passed. |
| `openspec validate add-geospatial-data-layers` | **Pass** — change valid. |
| `make openspec-gate CHANGE=add-geospatial-data-layers` | **Pass** — code review, verification records, and traceability accepted; gate notes recorded judgments are not authenticated. |

The corrected browser smoke bounds-checks the first Polygon position; this catches the synthetic EPSG:3826 coordinates when transformation is omitted, but does not validate every vertex or prove CRS independently.
