# Rodent Report Fixture Acceptance

**Status: READY FOR HUMAN REVIEW**\
**Scope:** fixture-only synthetic report-shaped data. No real citizen-report source was downloaded, read, stored, or imported.

## Implemented and verified

- Source investigation: `docs/evidence/rodent-report-source-investigation-2026-10-17.md`; Rat Radar, Taipei open-data, and 1999 candidates remain `UNVERIFIED` for license/privacy/schema/CRS/coverage. Real ingestion requires written authorization, privacy/retention review, field semantics, CRS/precision, and human acceptance.
- Pinned fixture: `services/api/tests/fixtures/rodent_reports/synthetic_reports.csv`, 5 rows, SHA-256 `611b8f66f023f96b745fd0bd7b01943629400bf837ad45283bde5b835505080d`.
- **Superseded 2026-10-26:** fixture regenerated to 160 synthetic rows (resource version `2026-10-26T17:22:26Z`, SHA-256 `b28305e75e02d88a0a18f5455ce2a8e26c6db47ab657e621cb3d63f39a84655d`) by `scripts/generate_synthetic_rodent_reports.py`. Shape uses only coarse aggregates recorded in `docs/evidence/ratdar-reuse-claim-2026-10-26.md`; no citizen-report record is stored, copied, or redistributed, and the reuse gate remains NO-GO/UNVERIFIED.
- Importer/API: additive migration `0004`, fail-closed exact-header importer, idempotent persistence, immutable provenance model and database mutation trigger, bounded bbox/time API, 5,000 cap, explicit empty/error states, and exact public allowlist.
- Dashboard: independent point layer, UTC temporal filters, selection/provenance, stale removal, synthetic limitations, and no simulation/infrastructure coupling.

## Verification

- Independent adversarial review: **PASS**, RR-001–RR-010 resolved.
- Public-health/privacy review: **PASS for fixture-only planning**; real-source integration remains blocked.
- Independent implementation review: **PASS**; CR-RR-001 resolved with frozen Pydantic provenance, DB immutability trigger, and regression test.
- QA: **CLEAR**; `make rodent-report-smoke` passed populated and storage-empty phases with live FastAPI/PostGIS/Next.js, no application API interception, actual point selection, temporal empty state, exact public allowlist, and cleanup.
- Python: QA recorded 166 passed; a later non-PostGIS run passed 162 / skipped 5 PostGIS-gated tests while Docker was unavailable.
- Web: 41 tests, typecheck, lint, format, build, and default E2E passed.
- OpenSpec validation: valid with three long-requirement warnings.
- Existing-layer smoke: `make geospatial-smoke` passed all four live administrative/stormwater populated/empty Playwright checks; temporary resources/listeners cleaned, shared PostGIS untouched.
- Quality gate: `make openspec-gate CHANGE=integrate-rodent-report-data` **PASS** after verification updates; gate records evidence and does not authenticate its source.

## Readiness boundary

The initial geospatial smoke attempt was interrupted by a Docker daemon outage. After Docker returned, only the old isolated test container, network, and disposable test database were removed. The follow-up `make geospatial-smoke` passed all four live administrative/stormwater populated and empty-state checks. Post-run verification found no smoke containers, volumes, networks, or listeners on ports 55439, 8000, and 3002; shared `infra-postgres-1` and `infra_ratsight-postgres-data` remained healthy and untouched.

The OpenSpec quality gate now **PASSES**. Change is Ready for Human Review, not project-owner acceptance. No real source integration, archive, or publication was performed. Real source terms, privacy, CRS, coverage, and public-health acceptance remain `UNVERIFIED`; explicit human authorization remains required before any real import.
