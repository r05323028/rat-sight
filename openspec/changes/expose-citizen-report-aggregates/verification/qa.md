# Verification — citizen-report aggregate layer

Scope: the de-identified 250 m aggregate authorized by the project owner on 2026-10-26. Not a review of the reuse claim itself, which stays unverified.

## What was run

| Check | Command | Result |
| --- | --- | --- |
| API tests | `cd services/api && uv run pytest -q` | 175 passed |
| Import/API aggregation tests | `uv run pytest tests/test_citizen_report_aggregates_import.py tests/test_citizen_report_aggregates_api.py -q` | 20 passed |
| API lint | `uv run ruff check`, `uv run ruff format --check` | clean |
| Web tests | `cd apps/web && npx vitest run` | 91 passed |
| Web typecheck | `cd apps/web && npx tsc --noEmit` | clean |
| Live import | `uv run python -m ratsight_api.importers.citizen_report_aggregates --source data/raw/ratdar_20261026_172226.csv` against `127.0.0.1:54330` | 91 rows, 319 reports, 1 version |
| Live endpoint | `GET /api/v1/citizen-report-aggregates?bbox=121.5,25.0,121.6,25.1` | 200, Polygon cells, full provenance |
| Browser probe | temporary Playwright spec, `PLAYWRIGHT_EXTERNAL_SERVERS=1 PLAYWRIGHT_PORT=3000`, desktop + mobile, deleted afterwards | 2 passed, zero console errors |

Probe assertions: `data_state=available`, `data_class=CITIZEN_REPORT_AGGREGATE`, `classification=UNVERIFIED`, non-empty features, `cell_size_meters=250`, first feature has no `location` property, geometry is `Polygon`, toggle enabled and checked, panel counts/suppression/non-observation text present, `data-citizen-aggregates="visible"`.

## What the tests actually pin

- Importer: dual suppression minimum, dropped private fields absent from the persisted batch and provenance, low-count report-type rows removed, invalid coordinates counted, wall-clock month bucketing, cell id prefix and cell height, provenance metadata, content hash, missing-column rejection, and fail-closed when nothing survives.
- Application/route: empty versus filter-miss distinction, exact public property set, invalid data class/classification rejected, storage errors mapped, bbox and month validation, 422 mapping.
- Web: layer renders fill+outline with the documented paint and gating, hidden state, panel counts and empty-no-substitution behaviour, badge/layer-row accounting.

## Observed import results (2026-10-26 export)

parsed 1435 · used 319 · invalid_coordinates 0 · suppressed_records 1116 · suppressed_cells 946 · rows 91 · versions 1 · months present: 2026-05 only.

## Unverified limits

- No independent privacy or legal review of the override; the reuse licence, grantor identity, retention/deletion obligations, and attribution requirements remain unverified.
- Month bucketing assumes Asia/Taipei wall clock because the export's offset is undocumented; cross-month boundary errors within one day are possible.
- The 250 m grid uses a latitude-anchored index, so cell width varies slightly with latitude (~250 m at 25°N).
- Only one month survives suppression, and the May 2026 volume reflects portal promotion/backfill; the layer cannot support any time-series or trend reading.
- No moderation-status, deduplication, or reporter-identity filtering is applied beyond coordinate/time validity, so counts include both 已審核 and 待審核 reports.
- Dashboard copy and provenance were checked in Chromium at two viewports only; no screen-reader or zoom audit was performed for this change.
