# Public-health suitability review: Taipei rodent-report sources

**Review date:** 2026-10-17

**Review mode:** Documentation and metadata only; no report rows, exports, photographs, or personal data accessed.

**Reviewer:** RatSight public-health analyst

## Scope and status vocabulary

`VERIFIED` below means established from the source investigation's documented landing-page/metadata checks on 2026-10-17, not that the underlying report data were validated. `UNVERIFIED` means the checked material did not establish the claim. `BLOCKED` means RatSight must not proceed until the named authorization or evidence exists.

This review relies on `docs/evidence/rodent-report-source-investigation-2026-10-17.md`, whose URLs and access boundaries are the source record for the findings below.

## Source A — Rat Radar / 見鼠雷達

**URLs checked (2026-10-17):** <https://ratdar.taipei/>, <https://ratdar.taipei/reports>, <https://ratdar.taipei/stats>, <https://ratdar.taipei/transparency>, and the export endpoint <https://ratdar.taipei/reports/export>. The prior investigation inspected public pages and an HTTP `HEAD` response only; it deliberately did not download the CSV.

| Question | Status | Finding |
|---|---|---|
| Public interface exists | VERIFIED | Public landing/report/statistics/transparency pages were reachable without login in the source investigation. |
| Report semantics | VERIFIED (interface only) | Visible categories include report time, type, location, status, photo, and description. Pending items are presented as unverified. |
| “Reported to 1999” meaning | VERIFIED (label only) | `已通報1999` is a submitter/status assertion; no independent municipal confirmation was established. |
| Moderation/confirmation validity | UNVERIFIED | AI screening and volunteer review are described, but sensitivity, specificity, agreement, species validation, and municipal confirmation were not established. |
| Ownership/endorsement | UNVERIFIED | Transparency text self-describes a citizen/non-profit project; Taipei City Government ownership or endorsement was not established. |
| License/reuse/redistribution | BLOCKED | No machine-readable license or written permission for RatSight reuse/redistribution was found. |
| Privacy/retention | BLOCKED | Privacy switch, names/photos, and public presentation are described, but no field-level processing, retention, security, or coordinate policy was verified. |
| CRS/geocoding/coverage | UNVERIFIED | Formal CRS, geocoding accuracy, completeness, and historical retention were not established. |
| Public-health suitability | BLOCKED for raw use | Opportunistic reports may support a separately authorized, coarse, descriptive report-activity layer only after privacy and semantic review. |

### Public-health interpretation

A platform-approved item is a moderation state, not a species-confirmed observation, infestation finding, prevalence estimate, incidence estimate, or causal intervention signal. Counts and maps would reflect reporting access, awareness, duplicates, geolocation, photo selection, moderation, and temporal behavior as well as any underlying events. “Statistics” must not be presented as prevalence, incidence, hotspot, risk, or treatment effect.

**Potentially suitable after authorization:** de-identified, coarse-grid/time-bucket report activity with source status, retrieval date, missingness/coverage caveats, and `UNVERIFIED` classification.

**Unsupported now:** raw reports, exact coordinates, names, photos, descriptions, public export, model movement weights, biological parameters, disease-risk inference, intervention-effect claims, or municipal confirmation claims.

## Source B — Taipei City open-data portal

**URLs checked (2026-10-17):** <https://data.taipei/> and portal rules <https://data.taipei/rule>. No rodent/1999 dataset was selected or downloaded.

| Question | Status | Finding |
|---|---|---|
| Portal reachable | VERIFIED | The portal is a discovery surface. |
| Relevant rodent dataset identified | UNVERIFIED | No dataset identifier/resource was established. |
| Publisher, license, schema, CRS, update cycle | UNVERIFIED | Generic portal pages do not establish these for a rodent dataset. |
| Completeness/privacy/redistribution | UNVERIFIED | No selected resource was assessed. |
| Public-health suitability | BLOCKED | Requires an authorized dataset-selection step and a field-level contract before access or interpretation. |

A portal listing alone is not proof that a dataset is complete, unrestricted for redistribution, or semantically a rodent observation source. If a future dataset is selected, preserve the publisher's event/status fields rather than translating service records into observations.

## Source C — Taipei 1999 complaints

**Discovery surfaces recorded (2026-10-17):** Taipei City 1999 service page <https://1999.gov.taipei/Front/main> (metadata-only HTTP HEAD/GET; HTTP 200; title `臺北市陳情系統1999`; description identifies the Taipei City Government petition/dispatch channel), <https://data.taipei/>, and <https://data.gov.tw/>. No specific rodent-complaint dataset or dataset endpoint was established, and no records were accessed.

| Question | Status | Finding |
| --- | --- | --- |
| Rodent complaint dataset identified | UNVERIFIED | No dataset ID, dataset endpoint, schema, or export was verified. |
| Complaint semantics | VERIFIED as a required distinction | A complaint/service request is not necessarily a sighting, inspection, treatment, or confirmed rodent observation. |
| License/privacy/CRS/coverage | UNVERIFIED | No resource-level terms were established. |
| Public-health suitability | BLOCKED | Requires official data-owner response/catalog record, de-identification and aggregation terms, and semantic validation. |

## Cross-source acceptable and prohibited use

### Suitable only after the relevant source gate

- Descriptive, clearly labeled **report activity** or **service-request activity** at approved coarse spatial/temporal resolution.
- QA of ingestion, provenance, filtering, and UI states using synthetic fixtures.
- Bias and coverage assessment where source metadata support it.

### Not supported by the reviewed evidence

- Calling reports `OBSERVED` without a documented observation/validation process.
- Species prevalence, incidence, infestation prevalence, population size, or disease risk.
- “Hotspot” or “high-risk area” claims from counts or maps.
- Causal claims about control actions or intervention benefit.
- Animal movement routes, movement weights, biological parameter calibration, or simulation inputs.
- Municipal confirmation inferred from platform approval, `已通報1999`, complaint status, or treatment/action labels.
- Identifiable or exact-location public display, raw export, photographs, names, phone/email, free-text descriptions, or unrestricted report redistribution.

## Required gate before any real-source work

1. Authored source-selection and data-owner decision.
2. Written license/reuse authorization and attribution requirements.
3. Field-level semantics for report, sighting, moderation, municipal confirmation, inspection, treatment, and duplicates.
4. Privacy decision covering allowed spatial/time precision, small-cell suppression, repeated-query controls, retention/deletion, access, and security.
5. CRS/geocoding, coverage, update cadence, missingness, and quality documentation.
6. Independent public-health/privacy acceptance and a versioned contract. Until all are present, source status remains `UNVERIFIED`/`BLOCKED` and no real records may be downloaded or imported.

## Evidence limits

This artifact does not establish that any candidate contains valid rodent observations, is representative of Taipei, is licensed for reuse, or is suitable for causal/public-health inference. It records metadata-level findings only and does not replace legal, privacy, data-owner, or human public-health review.
