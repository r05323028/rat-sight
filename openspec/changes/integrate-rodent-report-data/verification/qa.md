# Independent QA — integrate-rodent-report-data (fixture-only rodent reports)

**Verdict: CLEAR** for the fixture-only rodent-report scope. The initial Docker limitation is
resolved by the follow-up existing-layer smoke recorded below.

- Qitem: `qitem-20261017064935-ed420527b4fd93c3`
- Evaluator: `verification.qa@rat-team`
- Candidate: uncommitted diff `openspec/changes/integrate-rodent-report-data` on `main` at
  `cd838a6`
- Date: 2026-10-17
- Scope: QA-boundary harness implementation plus independent inspection and execution. No
  application implementation file was edited.

## QA-boundary deliverables

Two files were implemented inside the QA boundary (no application code changed):

- `scripts/rodent_report_smoke.sh` — isolated fixture-only smoke harness
  (`ratsight-rodent-report-smoke-${BASHPID}`, DB `55448`, API `8008`, web `3008`, disposable
  named volume, migrations, production importer/API, live Next.js, basemap style stubbed
  only, no application API interception, `down -v --remove-orphans` and listener/process
  cleanup on exit, fail-closed when Docker/ports are unavailable).
- `apps/web/e2e/real-rodent-report.spec.ts` — two gated live tests: populated
  (available + in-filter-empty) and storage-empty.

The command is `bash scripts/rodent_report_smoke.sh` / `make rodent-report-smoke`.

## Commands and results

| # | Command | Result |
|---|---------|--------|
| V1 | `make rodent-report-smoke` (populated run) | **1 passed, 1 skipped** — available + in-filter-empty |
| V2 | `make rodent-report-smoke` (cleared run) | **1 passed, 1 skipped** — storage-empty |
| V3 | `uv run pytest -q` | **166 passed** |
| V4 | `corepack pnpm --filter @ratsight/web test` | **3 files / 41 tests passed** |
| V5 | `corepack pnpm --filter @ratsight/web typecheck` | **pass** |
| V6 | `corepack pnpm --filter @ratsight/web lint` | **pass** |
| V7 | `corepack pnpm --filter @ratsight/web format:check` | **pass** (Prettier clean) |
| V8 | `corepack pnpm --filter @ratsight/web build` | **pass** (exit 0 twice, including after clearing `.next`) |
| V9 | `corepack pnpm --filter @ratsight/web e2e` (default) | **5 passed, 7 skipped** (external specs skip by design) |
| V10 | `openspec validate integrate-rodent-report-data` | **valid**; 3 long-requirement warnings |
| V11 | `uv run basedpyright` | **0 errors, 0 warnings, 0 notes** |
| V12 | `uv run ruff check`/`format --check` on feature files; `bash -n` smoke script | **clean / OK** |
| V13 | `make geospatial-smoke` | **4 Playwright tests passed** against live PostGIS/API/UI: administrative populated/empty and stormwater populated/empty; isolated resources and listeners cleaned; shared database untouched |
| V14 | `openspec validate integrate-rodent-report-data` | **valid**; 3 long-requirement warnings (rerun after verification updates) |
| V15 | `make openspec-gate CHANGE=integrate-rodent-report-data` | **PASS**; 7 recorded verification runs; recorded references/judgments are not authenticated by the gate |

### What the smoke asserts (V1/V2)

- Waits for the live `/api/v1/rodent-reports` 200 response; only
  `**/gl/positron-gl-style/style.json` is stubbed — no application API route is intercepted.
- Contract: `data_state=available`, `data_class=RODENT_REPORT`, `classification=SIMULATED`,
  `feature_count=5`, `bbox` present, `provenance.source_kind=synthetic_fixture`,
  `provenance.synthetic=true`, 64-hex `content_sha256`, first feature `Point`
  `[lon, lat]`, and the exact public property allowlist.
- Privacy: `longitude`, `latitude`, and `source_record_id` are **not** feature properties.
- Selection: enables the independent toggle, checks `RODENT_REPORT · SIMULATED` and the
  synthetic disclaimer, focuses and activates the `RR-0001` list button, asserts
  `aria-pressed=true`, and inspects report ID/type/time in the panel.
- Temporal filter: `reported_from=2026-10-10T00:00:00Z` yields `data_state=available`,
  `feature_count=0`, and "No reports in filters" with the previous selection/details removed;
  `reported_from=2026-10-01T00:00:00Z` (inclusive lower bound) restores all 5.
- Storage-empty (V2): `data_state=empty`, zero features, `provenance=null`,
  "No synthetic rodent reports have been imported.", and a disabled toggle — no fabricated
  points.

### Cleanup (V1/V2)

Post-run checks after the passing smoke: **no listeners on 55448 / 8008 / 3008**, **no
`ratsight-rodent-report-smoke` containers or volumes**, and the shared dev
`infra-postgres-1` container and `infra_ratsight-postgres-data` volume untouched. Cleanup
also ran after an earlier failed attempt (see limitations), so the harness is tolerant of a
failing test run.

## Independent implementation inspection

- **Migration/model:** `0004_rodent_reports` is additive with `Geometry(..., spatial_index=False)`
  plus explicit GiST and `(dataset_id, resource_version, reported_at)` indexes; CHECK
  constraints enforce `data_class='RODENT_REPORT'`, POINT geometry, and the epistemic
  vocabulary.
- **Importer:** pins the fixture dataset/version/SHA-256, validates the exact CSV header,
  unique IDs, RFC3339 UTC timestamps, finite EPSG:4326 coordinates, and bounded enums, rejects
  unknown/forbidden columns, and fails closed without partial writes. No real download or
  source-override path exists.
- **API:** validates bounded EPSG:4326 bbox (finite, range, order, ≤0.30°) and inclusive
  `reported_from`/`reported_to` with `from <= to`; deterministic `reported_at, report_id`
  ordering; 5,000 cap with `truncated`; filter echo; `data_state=empty` storage vs
  `available` in-filter miss; 422 for invalid input, 503/500 for storage/data failures. No
  personal or importer-only properties are serialized.
- **Frontend:** independent rodent toggle/layer with stale-layer removal, viewport querying,
  UTC `datetime-local` controls normalized at minute precision, and exact
  `RODENT_REPORT`/`SIMULATED` limitation wording; administrative, stormwater, and simulation
  layers remain separate. No heatmap, clustering, risk score, graph edge, or simulation input.
- **Source boundary:** only the committed synthetic fixture was used; no real citizen-report
  source was downloaded, read, or imported.

## Findings

### QA-RR-001 — RESOLVED — existing-layer smoke rerun after Docker outage

The original `make geospatial-smoke` attempt stopped when the Docker daemon became unavailable:

```text
Cannot connect to the Docker daemon at unix:///Users/seanchang/.docker/run/docker.sock.
Is the docker daemon running?
make: *** [geospatial-smoke] Error 1
```

That attempt left an isolated project (`ratsight-geospatial-smoke-66769`) whose container held
port 55439. After Docker returned, only that project's container, network, and disposable test
database volume were removed. The follow-up `make geospatial-smoke` completed successfully,
applying migrations through `0004_rodent_reports` and passing all four live Playwright checks:

| Test | Result |
|---|---|
| `e2e/real-api.spec.ts` — administrative data from running FastAPI API | **1 passed** |
| `e2e/real-api-empty.spec.ts` — empty administrative dataset | **1 passed** |
| `e2e/real-stormwater.spec.ts` — stormwater data from running FastAPI API | **1 passed** |
| `e2e/real-stormwater-empty.spec.ts` — empty stormwater storage, no fabricated lines | **1 passed** |

The follow-up used isolated project `ratsight-geospatial-smoke-35020`. Post-run checks confirmed
no containers, network, or volume remained for either smoke project; no listeners remained on
55439, 8000, or 3002; and shared `infra-postgres-1` / `infra_ratsight-postgres-data` remained
untouched (`healthy`). This verifies the live administrative and stormwater paths. Simulation
preview remains covered by V3 backend API tests and V9 dashboard E2E; this follow-up was not a
live simulation integration test. No real report source was downloaded, read, or imported.

### QA-RR-002 — OBSERVATION — one transient web build failure, not reproduced

A single `next build` returned exit 1 in a batch that also ran a dev server; two subsequent
builds, including one after `rm -rf apps/web/.next`, returned exit 0. Not reproduced; recorded
for transparency only.

### Standing repo hygiene (outside this change)

Untracked `.agents/skills/sem/**` and `skills-lock.json` still break repo-wide
`ruff check .` (13 E501) and `ruff format --check .` (4 files); feature files are clean.

## Limitations

- The fixture-only contract was verified against the 5-row synthetic fixture; real report
  sources remain out of scope and `UNVERIFIED` by design, and must not be imported without a
  new authorized contract.
- Stale-layer removal on empty/unavailable responses is covered by unit/source inspection; the
  live smoke asserts the user-visible empty-state and removed list/details, not MapLibre
  internals.
- Follow-up `make geospatial-smoke` verified live administrative and stormwater populated/empty paths. Simulation preview remains covered by the recorded backend API tests and dashboard E2E; this follow-up was not a live simulation integration test.

## QA position

The fixture-only rodent-report slice is CLEAR: harness, live smoke, backend/frontend suites,
independent inspection, and follow-up existing-layer smoke all pass. The geospatial smoke
verified live administrative and stormwater populated/empty paths; simulation preview remains
covered by existing backend and dashboard tests. No real-source use occurred.
