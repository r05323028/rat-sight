# Evidence Comparison

Verification date: 2026-10-17. Detailed source notes: `docs/evidence/rodent-report-source-investigation-2026-10-17.md`.

## Candidate comparison

| Candidate | Verified findings | Unverified / blocked | Suitability now |
|---|---|---|---|
| Rat Radar / 見鼠雷達 | Public Taipei-focused site; pages expose report categories/statuses; transparency page describes AI/volunteer review; export endpoint advertises CSV via metadata/header inspection. URLs: <https://ratdar.taipei/>, <https://ratdar.taipei/transparency>, <https://ratdar.taipei/reports/export>. | Independent authority/endorsement, license, automated retrieval and redistribution, privacy/retention, CRS/geocoding precision, completeness, schema, and update contract are not verified. Public moderation is not municipal confirmation. | **PROMISING BUT BLOCKED**. Best candidate for a future authorized, coarse/de-identified extract; raw ingestion is NO-GO. |
| Taipei City open-data portal | Portal endpoint <https://data.taipei/api/v1/dataset/search> returned JSON and `count: 0` for `鼠`, `鼠患`, `1999`, `病媒`, and `環境衛生` on 2026-10-17. | Zero keyword matches do not prove absence. No relevant dataset/resource ID, publisher contract, license, fields, CRS, coverage, or update terms verified. | **UNVERIFIED**. No selected source and no ingestion target. |
| Taipei 1999 complaints | Page <https://1999.gov.taipei/Front/main> returned HTTP 200; metadata identifies Taipei City 1999 petition/dispatch service (2026-10-17). Complaint semantics are service request/report, not confirmed sighting or inspection. | No specific dataset ID/API/schema/export, license, privacy, CRS, precision, historical coverage, or update terms verified. | **UNVERIFIED / BLOCKED**; page reachability is not dataset approval. Pending data-owner response; prefer aggregates or coarse de-identified output. |
| Other official environmental/sanitation sources | Existing source policy identifies government open-data, environmental, public-works, and hydrometeorological catalogs as contextual discovery points. | No additional source was verified as rodent evidence in this phase; infrastructure/covariate data must not be relabeled as rodent observations. | **NOT READY** for rodent ingestion. |

## Interpretation

Rat Radar is the most promising discovery candidate because it exposes report-shaped metadata and a documented moderation surface, but its authority, license, privacy controls, CRS/precision, and redistribution permission remain unresolved. The portal search provides useful negative evidence only about five exact keyword queries at one time. A 1999 case, if made available, would be a service-request record and must retain that semantics. None of these sources supports prevalence, infestation, population, movement, risk, or causal claims without separate validation.

## Recommendation: conditional NO-GO

Do not ingest or redistribute any real records in the current phase. Seek written authorization from the Rat Radar publisher first, or an official Taipei data-owner response for a de-identified 1999/open-data extract. The authorization request must cover permitted automated retrieval, license/attribution, field-level privacy, retention, spatial aggregation, CRS, schema, moderation/status meanings, duplicate handling, historical scope, and update cadence.

If authorization is granted, Rat Radar is the recommended first target only as a limited coarse-grid or aggregate `UNVERIFIED` report layer. It must not reuse synthetic fixture provenance or `SIMULATED` classification.
