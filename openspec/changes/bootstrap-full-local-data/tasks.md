# Tasks

## Specification

- [x] 1. Record verified source identities, existing importer behavior, runtime ownership boundaries, and candidate-layer constraints.
- [x] 2. Define persistent profile, inspect-only/mismatch behavior, optional synthetic loading, inventory, and bounded dashboard requirements.
- [x] 3. Resolve adversarial review findings into implementation and verification gates.

## Implementation

- [x] 4. Add project-scoped persistent Compose/bootstrap command with ownership-safe ports, migrations, and inventory output.
  - `scripts/data_bootstrap.sh` (up/status/down, `--inspect-only`, `--synthetic`, `--purge`)
  - `infra/docker-compose.full-local.yml` (project `ratsight-full-local`, volume `ratsight-full-local-postgres-data`, port 54330)
  - `Makefile` target `data-bootstrap` (+ `bash -n` in `validate`)
- [x] 5. Reuse pinned administrative and stormwater importers with a two-source inspect-only preflight before writes, source verification, idempotent rerun, and fail-closed mismatch handling.
- [x] 6. Add explicit opt-in synthetic fixture loading and document restart/teardown/data locations without committing raw sources.
  - `docs/infrastructure/full-local-data-bootstrap.md` (profile, sources, idempotency, non-atomicity, restart, teardown, inventory limits)
- [x] 7. Add only necessary dashboard/runtime integration for populated reference-layer status, provenance, bounded queries, and truncation semantics.
  - `apps/web/src/components/dashboard.tsx` reports returned stormwater counts/truncation; `apps/web/src/components/map-view.tsx` fits off-screen selected districts without changing bounded queries; focused component tests cover both.
- [x] 8. Document candidate sewer/manhole/trash-bin assessment and recommended next layer without ingesting unresolved sources.
  - `docs/infrastructure/full-local-data-bootstrap.md` candidate table; no importer, schema, or data added.

## Verification

- [x] 9. Run focused importer/bootstrap tests, lint/type/build, and OpenSpec validation.
  - `verification/qa.md`: 6 bootstrap tests, 60 frontend tests, typecheck, lint, build, and OpenSpec validation all pass.
- [x] 10. Verify clean bootstrap, exact pinned inventory, idempotent rerun, API/Web restart persistence, preflight mismatch and post-first-write failure behavior, and ownership-safe cleanup.
  - `verification/qa.md`: clean 12/19,747 bootstrap, idempotent rerun, API/Web restart, mismatch preflight, post-first-write conflict, purge/recreate, and shared-resource isolation all verified.
- [x] 11. Obtain independent QA and Municipal Analyst browser verification on the persistent populated runtime; record synthetic/reference limitations.
  - `verification/qa.md`: independent browser review passed district/pipeline selection, provenance, bounded/truncated behavior, and reference-only limitations.
- [x] 12. Run the quality gate and stop at Ready for Human Review; do not archive without owner approval.
  - `make openspec-gate CHANGE=bootstrap-full-local-data` → PASS. Traceability retains explicit partial limits for unpopulated/error UI states and candidate absence automation.
