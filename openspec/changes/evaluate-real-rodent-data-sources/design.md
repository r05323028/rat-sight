# Design

## Evidence method

Use authoritative landing pages, catalog/API documentation, terms/licences, privacy notices, and non-sensitive metadata. Each factual claim records URL and verification date. Safe metadata requests may verify endpoint existence; raw citizen-report payloads and exports remain out of scope.

## Candidate comparison dimensions

For each candidate record ownership/authority, public access method, stable identifiers, licensing and automated-retrieval permission, privacy exposure, geographic/temporal semantics, CRS and precision, update and historical coverage, moderation/confirmation meaning, bias and missingness, technical feasibility, and unresolved authorization.

Status vocabulary is explicit: `VERIFIED`, `UNVERIFIED`, `BLOCKED`, or `NOT APPLICABLE`. Public accessibility is not treated as reuse permission. Platform moderation is not municipal confirmation. A report is not automatically an observation or population estimate.

## Proposed next-contract boundary

**Unknown blocks implementation.** A future gate must receive all items below as an authored source contract; this checklist is not authorization to implement.

- **Identity/access:** publisher and owner, canonical dataset/resource IDs and URLs, documented retrieval method, resource version, retrieval timestamp, content hash, update cadence/history, and retention/deletion behavior.
- **Permission:** written data-owner authorization, licence/reuse and attribution terms, automated-retrieval permission, redistribution scope, security/access controls, and legal/privacy acceptance.
- **Input/public fields:** allow only approved stable source or aggregate ID, event category, source status, approved time bucket, approved spatial cell, and uncertainty/missingness fields. Explicitly forbid names, contacts, photographs, descriptions/free text, exact addresses, and exact points.
- **Semantics:** map report, sighting, platform moderation, municipal confirmation, inspection, treatment, duplicate, and deletion states separately. Default `data_class=RODENT_REPORT`, `classification=UNVERIFIED`; never `SIMULATED` or `OBSERVED` without an approved validation protocol.
- **Spatial:** admin unit or coarse grid only; documented EPSG/CRS or geocoding method, rounding/precision, coverage/bbox definition, aggregation threshold, and small-cell suppression/query protections.
- **Temporal:** timezone, timestamp precision, bucket and interval semantics, historical coverage, missingness, and correction/deletion handling.
- **Validation/provenance:** schema/version, required fields, duplicate policy, QA counts and validation method, source status, uncertainty, processing, failure/empty semantics, and reproducible update identity.
- **API boundary:** expose only approved aggregate/coarse fields; distinguish unavailable, storage-empty, filtered-empty, and error; preserve provenance and never expose forbidden source payloads.

If no candidate meets these conditions, the current recommendation is **NO-GO** for real download, ingestion, redistribution, and model use.
