# Adversarial Review — Public Health and Privacy

**Decision: NEEDS AMENDMENT before implementation**

## Review boundary and evidence

This review covers public-health interpretation, citizen-report versus observation semantics, privacy/minimization, spatial and temporal disclosure, acceptable labels, and prohibited claims. It inspected:

- `docs/evidence/rodent-report-source-investigation-2026-10-17.md` (source discovery record, 2026-10-17)
- `openspec/changes/integrate-rodent-report-data/proposal.md`
- `openspec/changes/integrate-rodent-report-data/design.md`
- `openspec/changes/integrate-rodent-report-data/tasks.md`

The source record explicitly says all candidates are `UNVERIFIED`, no report rows or personal data were downloaded, and no source has verified reuse, privacy, schema, CRS, or coverage terms. This review does not authorize source selection, real-data ingestion, or a policy choice.

## Findings

### PH-001 — BLOCKING: report events must not be represented as biological observations

The design correctly requires a future authorized citizen extract to default to `UNVERIFIED`, but it does not make the semantic boundary an end-to-end requirement. A citizen report is a submitted claim/event; it is not a species-confirmed sighting, inspection finding, treatment record, prevalence estimate, or infestation location. The evidence record makes this distinction explicit, including the warning that Rat Radar's `已通報1999` is a submitter/status assertion rather than independent confirmation.

**Required amendment:** Define the domain vocabulary and preserve it in storage, API, and UI: `report_event`/`report_type`, publisher moderation state, municipal status (if supplied), and biological confirmation must be separate nullable fields. Prohibit naming the layer “observations” or rendering “confirmed” unless a documented validation rule and human acceptance exist. Add contract tests for the distinction.

### PH-002 — BLOCKING: privacy and aggregation policy is not implementable

The design says “aggregate or coarse-grid” for a future real extract and excludes names, phones, photos, free-text addresses, and exact personal information, but does not specify minimum aggregation, small-cell suppression, temporal aggregation, query-result suppression, or protections against repeated narrow queries. An opaque ID plus a point and timestamp can still enable linkage or re-identification. The evidence record also notes that the source exposes photos, descriptions, names/privacy controls, and an export endpoint, with no verified retention or data-processing policy.

**Required amendment:** Add an explicit privacy decision before any real-source work: permitted spatial precision, permitted time precision, minimum cell/count threshold or suppression rule, repeated-query/rate-limit policy, retention/deletion, access roles, and whether a public API is allowed. If these values are not yet approved, represent them as `UNVERIFIED`/unknown and block real ingestion. Fixture-only data may use synthetic points but must not be used to claim that the real-data privacy policy is solved.

### PH-003 — HIGH: spatial precision and API disclosure are underspecified

`location_precision` is named but its allowed values and transformation rules are absent. A bounded EPSG:4326 bbox and 5,000-feature cap limit load, not disclosure. Returning point geometries and `source_record_id` can disclose a report location even when the UI says “coarse-grid.”

**Required amendment:** Define an allowlist of spatial precision classes and a deterministic de-identification transformation for any future authorized source. State whether the API can return geometry, and enforce the selected precision/suppression policy server-side rather than relying on the dashboard. Exact coordinates from the candidate citizen source must remain prohibited unless a separately approved privacy review permits them.

### PH-004 — HIGH: moderation and agency statuses need non-collapsing semantics

The evidence distinguishes pending/unverified, platform-approved, `已通報1999`, and possible municipal actions. The design has one `review_status`, which risks collapsing platform moderation, submitter assertion, and agency confirmation into one confidence-like field.

**Required amendment:** Use separately named fields/enums for source moderation, submitter report type, agency/1999 status, and biological validation. Document that “approved” means platform workflow only, not truth, municipal confirmation, or infestation. Missing/unknown statuses must remain explicit; do not infer a stronger status from a report page or aggregate.

### PH-005 — HIGH: source authorization is a hard gate, not only a future caveat

The proposal says real data requires authorization, license/reuse terms, privacy review, semantics, CRS/precision, and human acceptance. The tasks nevertheless proceed directly from investigation to implementation without a named gate artifact or acceptance owner. The evidence record's return criteria require an authored data-owner/PM decision and written terms.

**Required amendment:** Add a pre-implementation task/gate requiring a source selection decision, written authorization/reuse terms, privacy/retention decision, schema/data dictionary, CRS and coverage statement, and named public-health acceptance. Until that gate is satisfied, implementation must be limited to synthetic fixture-shaped records and must not test against downloaded real reports.

### PH-006 — HIGH: acceptable labels and prohibited claims need a normative contract

The proposal correctly excludes prevalence, population, movement, disease risk, and intervention evidence, but does not specify all UI/API wording. Report counts, maps, “hotspots,” or time series can be interpreted as prevalence/incidence or risk even without a formal risk score. Opportunistic reporting is affected by access, awareness, duplicate, geolocation, photo-selection, moderation, and temporal biases (evidence record).

**Required amendment:** Add a shared acceptable-label/prohibited-claim table. Acceptable examples: “citizen reports submitted to [publisher],” “platform status,” “synthetic report-shaped fixture,” and “coverage/validation unknown.” Prohibit “infestation,” “prevalence,” “incidence,” “risk,” “hotspot,” “confirmed rodent location,” “disease,” causal intervention benefit, and migration/movement claims unless separately evidenced and approved. Add UI/API tests that classification and limitation text are present.

### PH-007 — MEDIUM: temporal fields may disclose reporters and imply unsupported trends

The API design exposes `reported_at` and time filters but does not define timezone, minimum temporal granularity, retention, or treatment of edits/duplicates. Exact timestamps can aid identification; daily/weekly counts can be misread as incidence when reporting propensity changes.

**Required amendment:** Require UTC normalization and a documented display/storage granularity for any real source, with suppression where necessary. Preserve source timestamps only if authorized; otherwise aggregate. Label temporal results as report activity, not disease or population trends, and retain duplicate/status semantics.

### PH-008 — MEDIUM: provenance and uncertainty must reach interpretation surfaces

Typed provenance is proposed, but the design does not require the UI to show publisher identity, retrieval time, source status, coverage limitations, validation state, and classification for every report result. `data_class=RODENT_REPORT` is not itself an evidence classification and must not be rendered as `OBSERVED`.

**Required amendment:** Require provenance and limitations in the API envelope and layer/selection UI. Keep `classification` (`SIMULATED` for fixtures; `UNVERIFIED` for unvalidated authorized reports) distinct from `data_class`. Include source and processing references without exposing restricted source fields.

## Positive controls already present

- The evidence record explicitly prohibits treating platform-approved reports as confirmed observations and recommends a coarse/aggregate `UNVERIFIED` layer.
- The proposal excludes simulation and infrastructure-topology integration.
- The design excludes names, phones, photos, free-text addresses, and exact personal information from the allowlist.
- The design requires fail-closed validation and additive/idempotent persistence for fixture-shaped imports.
- The current project policy distinguishes `OBSERVED`, `INFERRED`, `SIMULATED`, and `UNVERIFIED`; the change should preserve this distinction at every boundary.

## Required changes before PASS

1. Amend proposal/design with the event-versus-observation vocabulary and non-collapsing status model.
2. Add an explicit privacy gate and implementable spatial/temporal disclosure policy, or keep real-source behavior blocked as unknown.
3. Add normative acceptable-label/prohibited-claim requirements and UI/API limitation tests.
4. Add source authorization and human public-health acceptance to the task/gate sequence.
5. Record the decision and any unresolved values as `UNVERIFIED`; do not silently choose thresholds, species, confirmation rules, or representativeness assumptions.

**Conclusion:** Synthetic fixture implementation can proceed only if it remains visibly `SIMULATED` and isolated. Any real citizen-report ingestion or public endpoint remains blocked pending the evidence, privacy, authorization, and human-review decisions above.

## Re-review addendum — 2026-10-17

The amended `proposal.md`, `design.md`, `specs/rodent-reports/spec.md`, and `tasks.md` were reviewed against PH-001–PH-008.

**Decision: PASS for fixture-only planning; real-source integration remains BLOCKED.**

Resolved in the amended artifacts:

- **PH-001 / PH-004:** The exact fixture contract now separates `report_type`, `review_status`, `municipal_status`, and `action_status`; the API/UI are required to state that `RODENT_REPORT` fixtures are not verified observations.
- **PH-002 / PH-003 / PH-007:** The input is pinned to a local synthetic CSV, exact forbidden fields are rejected, synthetic coordinates are explicitly non-real, and bounded EPSG:4326 plus inclusive UTC query behavior and stale/empty states are specified. The spec blocks real records until authorization and privacy/reuse contracts are verified.
- **PH-005:** The proposal/spec require data-owner authorization, license/reuse terms, privacy/retention review, field semantics, CRS/precision, and human acceptance before any real source. Tasks explicitly prohibit real downloads/imports and require a Ready for Human Review gate.
- **PH-008:** `RodentReportProvenanceV1`, `RODENT_REPORT`, and `SIMULATED` are mandatory and provenance is required at the API/dashboard boundary.

Remaining required clarification before any future real-source contract (not a blocker to the synthetic fixture plan):

1. A real-source proposal must define minimum spatial/temporal aggregation, small-cell suppression, repeated-query controls, retention, access, and deletion; the current design correctly does not invent these values.
2. UI/API copy should retain an explicit prohibited-claims list including “infestation,” “prevalence,” “incidence,” “hotspot,” “risk,” “confirmed rodent location,” disease, causal intervention benefit, and migration claims. Current wording prohibits prevalence/population/movement/risk but does not enumerate every term.
3. The committed fixture and manifest named by the design are implementation prerequisites; their absence in the planning tree is acceptable only if task 4 creates them before importer/API work and the hash/record manifest is independently verified.

No real source was downloaded or imported during this review. `git diff --check` and `openspec validate integrate-rodent-report-data` pass.
