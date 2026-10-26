# Tasks

## Specification

- [x] 1. Record the source, export hash, privacy findings, and the asserted-but-unverified reuse status in `docs/evidence/ratdar-reuse-claim-2026-10-26.md`, and record the owner override that authorizes a suppressed aggregate.
- [x] 2. Fix the aggregation contract in `design.md`: 250 m cells, monthly wall-clock buckets, report-type mapping, dual suppression minimum, dropped fields, and the never-a-simulation-input boundary.
- [x] 3. Write `specs/citizen-report-aggregates/spec.md` with import, API, and dashboard requirements plus scenarios.

## Implementation

- [x] 4. Add domain constants in `services/api/src/ratsight_api/domain/citizen_report_aggregates.py` (cell size, suppression, report-type codes, dropped fields, attribution, notice, bounds, caps).
- [x] 5. Add `CitizenReportCell` to `services/api/src/ratsight_api/infrastructure/database/models.py` with classification/data-class checks, `report_count >= 3`, unique key, GIST + version/month indexes.
- [x] 6. Add migration `services/api/alembic/versions/0007_citizen_report_cells.py` including the immutability trigger.
- [x] 7. Add the aggregating importer `services/api/src/ratsight_api/importers/citizen_report_aggregates.py` (`--source`, `--inspect-only`) that drops place/free-text/photo fields before writing and persists idempotently.
- [x] 8. Add `services/api/src/ratsight_api/application/citizen_report_aggregates.py` with bbox/month parsing, latest-version serving, empty-vs-filter-miss distinction, and the 5,000-feature cap.
- [x] 9. Add `GET /api/v1/citizen-report-aggregates` in `services/api/src/ratsight_api/api/routes/citizen_report_aggregates.py` and register it in `api/router.py`.
- [x] 10. Add typed schemas (`CitizenReportProvenanceV1` and the response models) to `services/api/src/ratsight_api/api/schemas.py`.
- [x] 11. Add `services/api/tests/test_citizen_report_aggregates_import.py` and `services/api/tests/test_citizen_report_aggregates_api.py`.
- [x] 12. Add web API types and `fetchCitizenReportAggregates` to `apps/web/src/lib/api.ts`.
- [x] 13. Add the MapLibre cell fill/outline layers and `data-citizen-aggregates` visibility marker to `apps/web/src/components/map-view.tsx`.
- [x] 14. Add the layer row, legend entry, panel, disclosure, and provenance details to `apps/web/src/components/dashboard.tsx`, plus the `citizen-aggregates` glyph and CSS.
- [x] 15. Extend `apps/web/src/components/dashboard.test.tsx` and `apps/web/src/components/map-view.test.tsx`.

## Verification

- [x] 16. Run `services/api` pytest (175 passed) and ruff check/format.
- [x] 17. Run `apps/web` vitest (91 passed) and `npx tsc --noEmit` (clean).
- [x] 18. Import the observed export into the full-local database (91 rows, 319 published reports, 1 version) and confirm the live endpoint returns Polygon cells with provenance.
- [x] 19. Run a temporary Playwright probe against the live app on desktop and mobile, then delete the probe spec.
- [x] 20. Update `docs/infrastructure/data-sources.md` and the evidence record with the override and its residual risk.

## Not done in this change

- [ ] Raise the reuse status above `UNVERIFIED` — needs grantor identity, licence/terms, attribution wording, retention/deletion obligations, and approved precision.
- [ ] Publish months other than 2026-05 — suppression leaves nothing else, and the May spike reflects portal promotion/backfill rather than measured rodent activity.
- [ ] Obtain independent privacy/legal review of the override; this change records it as an owner decision, not a cleared compliance position.
