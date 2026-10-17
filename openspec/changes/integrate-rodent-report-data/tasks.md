# Tasks

## Specification

- [x] 1. Investigate Rat Radar, Taipei open-data, and Taipei 1999 candidates; document license, privacy, semantics, CRS, coverage, and blockers in `docs/evidence/rodent-report-source-investigation-2026-10-17.md`.
- [x] 2. Define the exact fixture-only contract, typed `RodentReportProvenanceV1`, enum/precision semantics, privacy allowlist, bounded API filters, UI state matrix, and explicit no-real-source boundary in `design.md` and `specs/rodent-reports/spec.md`.
- [x] 3. Obtain independent adversarial and public-health/privacy review; resolve RR/PH findings before implementation.

## Implementation

- [x] 4. Add the committed synthetic fixture, manifest/hash README, additive migration/model, typed provenance schemas, and fail-closed local importer. The importer must reject non-fixture identities and forbidden fields; no real source download is permitted.
- [x] 5. Add the versioned spatial/temporal API with deterministic ordering, 5,000 cap, filter echo, explicit data states, and storage/error handling.
- [x] 6. Add the independent MapLibre report-point layer, UTC temporal controls, selection/provenance panel, exact limitation wording, stale-layer removal, and preserve administrative/stormwater/simulation independence.

## Tests and verification

- [x] 7. Add importer/schema tests: exact fixture hash/record manifest, invalid coordinates/timestamps/enums, duplicate IDs, changed hash, forbidden columns, and no partial writes.
- [x] 8. Add API tests: bbox ranges/spans/order, inclusive UTC boundaries, invalid ranges (422), storage failure, empty-vs-filter-empty, deterministic cap/truncation, filter echo, and no forbidden properties.
- [x] 9. Add UI/unit/browser tests and `scripts/rodent_report_smoke.sh`: it must use compose project `ratsight-rodent-report-smoke-$BASHPID`, ports 55448/8008/3008, a disposable named volume, migrations, `seed_rodent_report_smoke.py`, production importer/API, and Playwright against the live app with only the basemap style stubbed. It must assert `RODENT_REPORT`/`SIMULATED`, selection, provenance, temporal filtering, empty/error states, and no fabricated geometry, then run `down -v --remove-orphans`, remove temporary files, and record cleanup/listener checks in `verification/qa.md`. The command MUST never download or read a real report source.
- [x] 10. Run backend/web suites, type/lint/format/build, existing geospatial smoke, and `bash scripts/rodent_report_smoke.sh`; record exact commands/results in `verification/qa.md`. Explicitly record that no real report source was downloaded or imported.
- [x] 11. Complete independent code review and QA, write `verification/traceability.md` and `verification/gate.json`, run `openspec validate integrate-rodent-report-data` and `make openspec-gate CHANGE=integrate-rodent-report-data`, and stop at Ready for Human Review. Do not archive or import real reports without explicit human authorization.
