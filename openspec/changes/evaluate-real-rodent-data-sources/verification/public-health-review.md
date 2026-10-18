# Public-health feasibility review — official complaint activity

**Review date:** 2026-10-18  
**Review boundary:** Independent assessment of the researcher feasibility artifacts and prior source investigation. Documentation and non-sensitive metadata only; no complaint rows, exports, photographs, names, descriptions, or exact locations accessed.  
**Decision:** **NO-GO for real-data ingestion; conditional future GO only for a bounded descriptive activity layer after human/data-owner approval.**

## Evidence reviewed

- `openspec/changes/evaluate-real-rodent-data-sources/evidence.md`
- `openspec/changes/evaluate-real-rodent-data-sources/recommendation.md`
- `openspec/changes/evaluate-real-rodent-data-sources/design.md`
- `openspec/changes/evaluate-real-rodent-data-sources/verification/source-comparison.md`
- `docs/evidence/rodent-report-source-investigation-2026-10-17.md`
- `docs/evidence/rodent-report-public-health-suitability-review-2026-10-17.md`

The researcher artifacts record the verification date as 2026-10-17 and identify URLs for each claim. Their status vocabulary is retained here: `VERIFIED` describes a documented interface/metadata fact, not validation of underlying records; `UNVERIFIED` means the contract or meaning is unresolved; `BLOCKED` means RatSight must not access or ingest until the named gate is met.

## Candidate assessment

### Rat Radar / 見鼠雷達

**Status:** Interface/report-shaped metadata `VERIFIED`; raw use **BLOCKED**.

The documented pages (<https://ratdar.taipei/>, <https://ratdar.taipei/reports>, <https://ratdar.taipei/transparency>) expose report categories/statuses and distinguish pending/unverified items. The export endpoint (<https://ratdar.taipei/reports/export>) advertised CSV metadata via HEAD inspection only; no CSV was downloaded.

Public-health interpretation remains constrained:

- A citizen submission is a report event, not necessarily a species-identified sighting, inspection, treatment, or confirmed observation.
- Platform AI/volunteer moderation is a workflow state; it does not establish sensitivity, specificity, species validity, municipal confirmation, or representativeness.
- `已通報1999` is a displayed submitter/status assertion, not evidence of an independently confirmed municipal case.
- Opportunistic reporting can vary with access, awareness, duplicates, geolocation, photo selection, moderation, and time. Counts cannot be interpreted as prevalence, incidence, infestation, hotspot, or risk.

License/reuse, automated retrieval, retention, security, CRS/geocoding precision, completeness, update contract, and redistribution permission remain unresolved. Therefore raw reports, photos, names, descriptions, exact coordinates, and public exports are excluded.

### Taipei open-data portal

**Status:** Candidate discovery only; **UNVERIFIED/BLOCKED**.

The researcher recorded the portal and rules surfaces (<https://data.taipei/>, <https://data.taipei/rule>) and a metadata search endpoint (<https://data.taipei/api/v1/dataset/search>) returning zero results for five exact keywords at the check time. This is limited negative evidence, not proof that no relevant resource exists. No dataset/resource ID, publisher contract, license, schema, CRS, coverage, update cadence, or privacy terms were established.

No complaint or rodent interpretation is permitted from the generic portal. A future selected resource must be assessed at resource level and preserve its original event/status semantics.

### Taipei 1999 complaints

**Status:** Service-page reachability `VERIFIED`; rodent dataset **UNVERIFIED/BLOCKED**.

The 1999 page (<https://1999.gov.taipei/Front/main>) was documented as HTTP 200 metadata-only access on 2026-10-17. This establishes a petition/dispatch service page, not a rodent dataset, API, export, license, or authorization. A complaint/service request is not necessarily a sighting, inspection finding, treatment action, or confirmed observation.

No use is permitted until a data-owner response or official catalog/resource record provides field semantics, permitted resolution, historical coverage, privacy/retention terms, and reuse authorization. Prefer aggregate or coarse de-identified activity over citizen-level records.

## Privacy and public-health risks

1. **Direct identifiers and sensitive content:** Names, contacts, photographs, descriptions/free text, and exact addresses/coordinates are excluded. Public visibility is not reuse permission.
2. **Location disclosure:** Exact or fine-grained points can identify households or reporters even without direct identifiers. A future contract must specify approved grid/admin-unit precision, coordinate transformation, minimum cell counts, and small-cell suppression.
3. **Temporal disclosure:** Exact timestamps can enable linkage and imply unsupported trends. A future contract must define timezone, time bucket, history, corrections, deletion, and retention.
4. **Status overinterpretation:** Moderation, complaint routing, inspection, treatment, and authority confirmation must be separate fields. No one status may be treated as biological truth.
5. **Repeated-query disclosure:** A public spatial/time API would need query bounds, suppression, rate/repeated-query controls, and access policy. A feature cap alone is not a privacy control.
6. **Coverage/reporting bias:** Missingness and reporting propensity must be documented before descriptive comparisons. No denominator, sampling frame, or completeness is currently verified.

## Suitable and unsupported uses

### Conditionally suitable after approval

- A descriptive layer named **municipal complaint activity** or **citizen report activity**, preserving source semantics.
- Coarse spatial/time aggregates or approved de-identified cells, with suppression and coverage caveats.
- Display of source status and provenance without translating it to observation truth.
- Data-quality, missingness, duplicate, and workflow-status QA once an authorized extract and data dictionary exist.

### Explicitly unsupported by current evidence

- Real-data download, scraping, import, storage, or redistribution now.
- `OBSERVED`, “confirmed rodent location,” species confirmation, infestation, prevalence, incidence, population, disease risk, or hotspot labels.
- Causal claims about control/treatment benefit or municipal intervention effectiveness.
- Animal movement routes, movement weights, biological parameter calibration, simulation inputs, or infrastructure connectivity.
- Public display of names, contacts, photos, descriptions, exact addresses, exact citizen coordinates, or raw exports.
- Treating report counts as rates without a verified denominator, coverage model, or sampling design.

## GO/NO-GO criteria

### Current decision: NO-GO

The following are absent, so no real-data implementation or access is authorized:

- authored source selection and data-owner approval;
- written license/reuse, automated retrieval, attribution, and redistribution terms;
- field-level data dictionary and separate report/service/moderation/inspection/treatment/confirmation semantics;
- approved spatial and temporal precision, small-cell/query suppression, retention/deletion, access, and security controls;
- verified CRS/geocoding, coverage, update cadence, duplicate/correction behavior, and missingness documentation;
- independent legal/privacy and public-health acceptance.

### Conditional future GO gate

A human-approved source contract must satisfy all items above and require a fail-closed, versioned, de-identified aggregate/coarse-cell extract. The first release must be descriptive only, carry `RODENT_REPORT` or an explicitly approved service-request class with `UNVERIFIED` classification, retain provenance and uncertainty, and remain disconnected from simulation, infrastructure topology, prevalence, risk, and causal analysis. Any unresolved item remains `UNVERIFIED`/`BLOCKED` rather than receiving an invented default.

## Verification note

This artifact records an independent public-health/privacy assessment of the documented feasibility evidence. It does not constitute legal authorization, data-owner approval, or validation of any rodent report. No raw data were accessed.
