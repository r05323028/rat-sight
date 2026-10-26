# Rodent report synthetic fixture

`services/api/tests/fixtures/rodent_reports/synthetic_reports.csv` is the only
permitted input for the fixture-only rodent-report importer. It is synthetic
report-shaped test data. It is **not** a rodent observation, prevalence,
population, movement, disease-risk, or intervention record.

## Pinned identity

- dataset ID: `00000000-0000-4000-8000-000000000002`
- resource version: `2026-10-26T17:22:26Z`
- content SHA-256: `b28305e75e02d88a0a18f5455ce2a8e26c6db47ab657e621cb3d63f39a84655d`
- records: 160

## Columns

`source_record_id`, `report_type`, `reported_at`, `longitude`, `latitude`,
`location_precision`, `review_status`, `municipal_status`, `action_status`.

All rows use `location_precision=synthetic_point`, `review_status=unreviewed`,
`municipal_status=not_assessed`, and `action_status=none_reported`. These are
fixture values, not claims about a real reporting system. Coordinates are
synthetic WGS84/EPSG:4326 points.

## Manifest check

```sh
sha256sum services/api/tests/fixtures/rodent_reports/synthetic_reports.csv
# b28305e75e02d88a0a18f5455ce2a8e26c6db47ab657e621cb3d63f39a84655d
```

Any change to the CSV requires updating this manifest and the importer constant.
No real citizen-report source may be substituted for this fixture.

## Provenance of the shape

The rows are regenerated deterministically by
`scripts/generate_synthetic_rodent_reports.py` (seed `20261026`). No record from
any citizen-report export is reproduced. Only three coarse aggregates documented
in `docs/evidence/ratdar-reuse-claim-2026-10-26.md` inform the shape: the
report-type mix, the monthly volume shape, and the time-of-day shape. Hotspot
centres are author-chosen plausible shopping/nightlife areas; every coordinate is
a jittered synthetic point (`location_precision=synthetic_point`) and none is an
observed location. Regenerate with:

```sh
uv run python scripts/generate_synthetic_rodent_reports.py --write
```
