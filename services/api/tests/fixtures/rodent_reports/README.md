# Rodent report synthetic fixture

`services/api/tests/fixtures/rodent_reports/synthetic_reports.csv` is the only
permitted input for the fixture-only rodent-report importer. It is synthetic
report-shaped test data. It is **not** a rodent observation, prevalence,
population, movement, disease-risk, or intervention record.

## Pinned identity

- dataset ID: `00000000-0000-4000-8000-000000000002`
- resource version: `2026-10-17T00:00:00Z`
- content SHA-256: `611b8f66f023f96b745fd0bd7b01943629400bf837ad45283bde5b835505080d`
- records: 5

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
# 611b8f66f023f96b745fd0bd7b01943629400bf837ad45283bde5b835505080d
```

Any change to the CSV requires updating this manifest and the importer constant.
No real citizen-report source may be substituted for this fixture.
