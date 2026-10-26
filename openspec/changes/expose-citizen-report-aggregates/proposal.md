# Proposal

## Why

Rat Radars citizen-report platform (見鼠雷達, `https://ratdar.taipei/`) publishes a report export that is technically usable but carries no verified reuse licence, grantor identity, retention policy, or coordinate-precision terms, and contains personal data: exact coordinates, free-text place names, and third-party photo URLs. The project owner therefore asked for a citizen-report layer, and authorized publishing a de-identified aggregate after being shown the blockers.

Evidence: `docs/evidence/ratdar-reuse-claim-2026-10-26.md` (`AUTHORIZATION=ASSERTED_BY_PROJECT_OWNER`, `EVIDENCE=ABSENT`, `REUSE=UNVERIFIED`), `docs/evidence/rodent-report-source-investigation-2026-10-17.md`, `openspec/changes/evaluate-real-rodent-data-sources/recommendation.md`.

## What Changes

- Add a local-file-only importer that aggregates a public citizen-report export into 250 m grid cells × month × report type counts, dropping place names, free text, and photo URLs before any write and never storing exact coordinates.
- Add additive PostGIS table `citizen_report_cells` (migration `0007`) with tamper-evident immutability and database-level suppression checks.
- Add `GET /api/v1/citizen-report-aggregates` with bounded bbox/months/report_type filters, typed `CitizenReportProvenanceV1`, and explicit empty/error states.
- Add an independent dashboard layer with its own toggle, suppression/what-was-dropped disclosure, attribution, and provenance details.
- Record the owner override in evidence and infrastructure documentation.

## Scope and Integrity Boundary

The aggregate is a report-density artifact, not an observation. It stays `data_class=CITIZEN_REPORT_AGGREGATE`, `classification=UNVERIFIED`, and is never `OBSERVED` or `SIMULATED`, never a simulation input, and never evidence of rodent abundance, density, prevalence, movement, intervention effect, or human risk.

Record-level ingestion, redistribution of the raw export, free text, photographs, and exact coordinates remain out of scope. The reuse blocker in `evaluate-real-rodent-data-sources` is not closed by this change: the owner override is recorded as an explicit, reversible exception scoped to suppressed counts, and attribution is credit, not a licence.
