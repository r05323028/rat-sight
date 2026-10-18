# Recommended next implementation boundary

## Decision

**NO-GO for real-data ingestion in this change.** Rat Radar is the most promising candidate for a future limited descriptive layer, but it is blocked by written reuse authorization, license, privacy/retention, spatial precision/CRS, schema, and update-contract gaps. Taipei open-data and 1999 candidates remain unverified and have no selected resource contract.

## Conditional future target

If a human approves source selection and the publisher/data owner supplies written terms, begin with a de-identified, coarse-grid or aggregate report-activity dataset. Preserve the source's event semantics (`report`, `service_request`, moderation, inspection, treatment) rather than translating them to observations.

Required minimum contract:

- source owner, dataset/resource identifier, version, retrieval timestamp, licence, attribution, and written automated-retrieval/redistribution permission;
- allowed fields limited to stable source ID or approved aggregate key, report/service category, source status, time bucket, approved spatial cell, and uncertainty/missingness metadata;
- no names, contact details, photos, descriptions/free text, exact addresses, or exact citizen coordinates;
- explicit CRS and approved spatial precision/aggregation, with WGS84 only after documented transformation if needed;
- timestamp timezone and inclusive/exclusive interval semantics;
- duplicate, moderation, deletion, retention, update, and correction behavior;
- classification `RODENT_REPORT` or an approved service-request class with `UNVERIFIED` unless an independent observation protocol is documented; never reuse synthetic fixture provenance or `SIMULATED`;
- fail-closed validation, provenance retention, and API states that distinguish unavailable, empty, and filtered-empty results.

## Human decisions required

1. Select Rat Radar, a specific Taipei open-data resource, 1999 extract, or NO-GO.
2. Approve permitted use, redistribution, retention, and attribution after legal/privacy review.
3. Approve spatial/time aggregation and small-cell/query protections.
4. Approve semantic treatment of moderation, service-request, inspection, and treatment statuses.
5. Approve whether any future output may be used only for descriptive exploration, or also for a separately validated research study. No movement, prevalence, risk, causal, or simulation use is implied by this recommendation.
