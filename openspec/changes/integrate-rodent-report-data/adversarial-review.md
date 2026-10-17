# Adversarial review — integrate rodent report data

**Reviewer:** verification-reviewer\
**Review type:** independent planning/specification re-review\
**Decision:** PASS — RR-001–RR-010 are resolved in the amended planning artifacts. The fixture-only planning contract is ready for implementation, subject to the remaining independent/public-health review gate.

## Evidence reviewed

- `proposal.md`
- `design.md`
- `specs/rodent-reports/spec.md`
- `tasks.md`
- `docs/evidence/rodent-report-source-investigation-2026-10-17.md`
- `openspec validate integrate-rodent-report-data` — valid, with three long-requirement warnings

The source investigation remains appropriately evidence-first: it did not download citizen records, does not call platform moderation an observation, and leaves Rat Radar, Taipei open-data, and 1999 candidates `UNVERIFIED`.

## Previous findings

### RR-001 — BLOCKING / HIGH / RESOLVED: typed provenance contract was missing

**Resolution verified:** `design.md` enumerates immutable top-level `RodentReportProvenanceV1`, exact nested processing/uncertainty fields, literal synthetic source/classification values, UUID/RFC3339/hash/CRS requirements, ownership, and feature-level provenance references. `tasks.md` requires schema tests.

### RR-002 — BLOCKING / HIGH / RESOLVED: synthetic fixture identity and manifest were unspecified

**Resolution verified:** `design.md` and `spec.md` pin the exact fixture path, dataset ID, resource version, and manifest location; `tasks.md` requires the committed fixture and hash README. The design requires default rejection of other identities and no real-source override flag.

### RR-003 — HIGH / RESOLVED: report semantics and enums were underspecified

**Resolution verified:** exact report, precision, review, municipal, and action enums are listed, with the fixture’s synthetic values and explicit warning that they are not real-system claims. The source investigation’s distinction between submitter status, moderation, and municipal confirmation is preserved.

### RR-004 — HIGH / RESOLVED: privacy controls were only negative statements

**Resolution verified:** exact input columns and public feature allowlist are specified; unknown columns and named forbidden fields are rejected; coordinates are synthetic WGS84 points; forbidden-field and no-serialization tests are required.

### RR-005 — HIGH / RESOLVED: bounded spatial/temporal API behavior was incomplete

**Resolution verified:** exact bbox finite/range/order/span rules, RFC3339 UTC normalization, inclusive filtering, `from <= to`, deterministic ordering, 5,000 cap, filter echo, empty-state distinction, HTTP 422, and non-2xx storage failure are now stated.

### RR-006 — MEDIUM / RESOLVED: dashboard state/temporal behavior was not testable

**Resolution verified:** UTC `datetime-local` controls, viewport querying/debounce, exact state classes, stale-point removal, selection, provenance, and explicit `RODENT_REPORT`/`SIMULATED` non-observation wording are specified; `tasks.md` requires browser smoke coverage.

### RR-007 — MEDIUM / RESOLVED: acceptance and traceability gates were missing

**Resolution verified:** `tasks.md` requires schema/fixture/privacy/API/UI tests, named isolated smoke evidence, no-real-source recording, independent review, QA/traceability artifacts, `verification/gate.json`, and Ready for Human Review without archiving or real import.

### RR-008 — HIGH / RESOLVED: public GeoJSON response and feature schema were not fully typed

**Resolution verified:** `design.md` and `spec.md` now define the serialized FeatureCollection envelope, exact top-level fields/types, feature type/id/2D geometry, filter echo null/string semantics, deterministic ordering, and property omission rules.

### RR-009 — MEDIUM / RESOLVED: temporal UI timezone and smoke command were underspecified

**Resolution verified:** UTC datetime-local controls now explicitly use minute precision, treat empty controls as omitted/all-time filters, and convert values to RFC3339 `Z`. `tasks.md` names `scripts/rodent_report_smoke.sh`, its project/ports/disposable volume, production-path setup, basemap-only stubbing, cleanup, listener checks, and evidence path.

## Remaining finding

### RR-010 — HIGH / RESOLVED: the public feature-property allowlist contradicted its coordinate/opaque-ID rules

**Resolution verified:** `design.md` and `spec.md` now enumerate the exact public keys: opaque `report_id`, `source`, six report-semantic fields, `data_class`, `classification`, and four provenance references. They explicitly keep `source_record_id`, `longitude`, and `latitude` importer-only, with coordinates represented only by 2D Point geometry. An exact-key contract test is required.

## Positive assessment

- The source investigation correctly records absent license/privacy/CRS/schema terms and does not fabricate report data.
- The proposal explicitly excludes real citizen-report ingestion, redistribution, prevalence, movement, disease-risk, intervention, topology, heatmaps, and simulation integration.
- The amended contract keeps synthetic `RODENT_REPORT` data separate from infrastructure and simulation and preserves `SIMULATED` classification.

## Return criteria

RR-001–RR-010 are resolved. The planning review is PASS for the fixture-only scope; implementation may proceed only through the specified test/evidence workflow and after the independent public-health/privacy review in task 3. No real-source ingestion or redistribution is authorized by this PASS.
