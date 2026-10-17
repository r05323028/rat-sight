# Independent implementation code review

**Reviewer:** verification-reviewer\
**Scope:** current rodent-report implementation diff and QA harness: migration/model/importer/API/schemas/tests, frontend API/dashboard/MapView/tests/E2E, fixture manifest, smoke script, and documentation.\
**Decision:** PASS.

## Review basis

The implementation was inspected independently against the amended fixture-only contract. No real report source was downloaded or imported by this review. The existing QA artifact reports isolated smoke execution and a Docker-outage limitation for the secondary geospatial smoke; those claims are not treated as independently rerun here.

## Findings

### CR-RR-001 — HIGH / RESOLVED: the declared immutable provenance envelope was mutable

**Resolution verified:** `RodentReportProvenanceV1` now uses `ConfigDict(extra="forbid", frozen=True)`, `test_provenance_model_is_immutable` verifies reassignment fails, and migration `0004_rodent_reports` adds the `rodent_reports_immutable` trigger preventing UPDATE/DELETE with downgrade cleanup.

## Positive observations

- Fixture identity, path, hash, and five-record manifest match: `shasum` produced `611b8f66f023f96b745fd0bd7b01943629400bf837ad45283bde5b835505080d`.
- Importer is local fixture-only in its production entry point, rejects unknown CSV headers, validates IDs/timestamps/enums/finite EPSG:4326 coordinates, and persists only synthetic `RODENT_REPORT`/`SIMULATED` records.
- API emits the exact public property set without `source_record_id`, longitude, or latitude properties; geometry is a bounded 2D Point. Bbox/time validation, inclusive filters, deterministic ordering, cap, filter echo, empty-state distinction, and storage/data errors are implemented.
- Dashboard derives visible selection from current query data, removes stale report points/layers, labels synthetic data, and keeps report points independent of stormwater, administrative, and simulation layers.
- Smoke harness uses a disposable compose project/ports and only stubs the external basemap; the live application API is not intercepted.

## Verification run

- `uv run --package ratsight-api pytest services/api/tests/test_rodent_reports_import.py services/api/tests/test_rodent_reports_api.py` — **48 passed, 2 skipped** (PostGIS-gated tests skipped in this environment).
- `corepack pnpm --filter @ratsight/web test -- --run` — **41 passed**.
- `corepack pnpm --filter @ratsight/web build` — **passed**.
- Targeted backend Ruff checks — **passed**.
- `openspec validate integrate-rodent-report-data` — **valid**, with three long-requirement warnings.
- `scripts/rodent_report_smoke.sh` — not rerun in this review; QA artifact reports populated and empty runs passed.

## Verdict

**PASS:** CR-RR-001 is resolved. Backend tests, frontend tests, build, and targeted Ruff checks pass. PostGIS-gated tests and the live rodent smoke were not rerun in this review; QA evidence reports them separately. Real-source ingestion remains prohibited. No implementation files were edited during review.
