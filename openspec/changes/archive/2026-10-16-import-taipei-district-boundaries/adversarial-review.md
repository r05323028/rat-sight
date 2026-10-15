# Adversarial Review

**Decision: PASS**

The planning artifacts are structurally valid (`openspec validate import-taipei-district-boundaries` passed), and the previously identified blocking contract/classification and provenance issues are resolved. Review scope was `proposal.md`, `specs/administrative-boundaries/spec.md`, `design.md`, `docs/evidence/taipei-district-boundaries-2026-10-15.md`, and the existing architecture/API/web context.

## Findings

### BND-001 — BLOCKING / HIGH / RESOLVED: classification contract contradicts project vocabulary

**Evidence:** `docs/evidence/taipei-district-boundaries-2026-10-15.md` previously labeled the administrative record `OBSERVED`, while `docs/architecture/overview.md` defines `OBSERVED` as a direct documented field observation and the project API currently constrains classification to `OBSERVED | INFERRED | SIMULATED | UNVERIFIED` (`services/api/src/ratsight_api/api/schemas.py`, `Classification`). The proposal/spec require an explicit administrative-reference classification distinct from rodent/infrastructure evidence.

**Resolution verified:** The amended artifacts define `data_class=ADMINISTRATIVE_REFERENCE` separately from epistemic `classification`, use `classification=UNVERIFIED` for unresolved currentness, and explicitly prohibit biological OBSERVED/INFERRED/SIMULATED representations. The evidence record now uses the same separation. Implementation must preserve these separate fields in persistence, API, GeoJSON, and UI.

### BND-002 — BLOCKING / HIGH / RESOLVED: source evidence was asserted as verified without reproducible verification

**Evidence:** The amended evidence record now includes retrieval, SHA-256, archive listing, and GeoPandas inspection claims. I independently retrieved the linked bytes on this review run: SHA-256 was `77bcc347b503b8ff8a43f7e1afaaedb18877a6222282587b145adaba69afd2d9`; the response was a ZIP containing the five expected shapefile members. Independent GeoPandas inspection resolved `EPSG:3826`, `(12, 19)`, 12 Polygon geometries, all valid, unique/non-null CPID, and non-null TNAME.

**Resolution verified:** The amended artifacts no longer present legal/current currency as established, retain the 2022-09-15 version and UNVERIFIED currentness, and require the importer to verify the recorded archive/hash. The evidence command block should still replace its `<download URL>` placeholder with the literal URL if it is intended to be copy/paste reproducible.

### BND-003 — HIGH / RESOLVED: provenance ownership was internally contradictory

**Resolution verified:** The amended design and spec now consistently select one complete version-1 provenance object at the GeoJSON top level. Feature properties contain only district identity, data class/classification, and source/version/hash references, and clients resolve full provenance from the top-level object. The exact JSON shape and immutability rule are defined in design.md.

### BND-004 — HIGH / RESOLVED: deterministic bounds and CRS/geometry safety were underspecified

**Resolution verified:** The amended design/spec define explicit EPSG:3826 source bounds `[296000, 2761000, 317500, 2790000]`, EPSG:4326 transformed bounds `[121.45, 24.94, 121.70, 25.23]`, fail-closed CRS/axis handling, finite/non-empty checks before and after transformation, unsupported-dimension/type rejection, no silent repair, and malformed fixtures. The envelopes are explicitly documented as validation margins rather than a district-count assertion.

### BND-005 — HIGH / RESOLVED: idempotency source-version/hash lifecycle and extracted-input verification conflict

**Resolution verified:** The amended design/spec now require the source archive (not an extracted directory) for import, reject a different archive hash for an existing dataset/resource version, require a new resource version for changed bytes, and define transactional upsert/rollback plus omitted-record behavior. The unique key and fail-closed hash policy are now deterministic. Implementation still needs the specified repeat/hash/content/omission tests.

### BND-006 — MEDIUM / RESOLVED: API empty, unavailable, and failure states were not distinct

**Resolution verified:** The amended design/spec define `data_state=empty|available`, HTTP 200 only for empty, non-2xx for storage/serialization failures, complete feature metadata, and no fallback geometry. The eventual implementation must retain this distinction in the Pydantic contract and tests.

### BND-007 — MEDIUM / RESOLVED: frontend interaction and verification criteria omitted lifecycle details

**Resolution verified:** The amended spec now requires post-style-load rendering, keyboard-accessible selection, loading/error/empty states, stale-layer removal, source/currentness display, and simulation-layer independence. The implementation still needs the specified frontend tests.

### BND-008 — MEDIUM / RESOLVED: identifier/name semantics

**Resolution verified:** The amended artifacts select `CPID` and `TNAME`, require UTF-8 decoding, Unicode NFC normalization, trimming, non-empty values, and unique normalized CPID values. Encoding and normalization failure behavior is fail-closed.

## Non-blocking observations

- The dedicated table and dataset-specific importer are proportionate to this one administrative layer and avoid an unnecessary generic ingestion framework. Keep them narrow; do not add scheduled downloads or generic synchronization.
- The additive migration and one-transaction import are consistent with the repository's no-reset/data-preservation policy, but the transaction/rollback behavior still needs the explicit tests in BND-005.
- The amended artifacts correctly keep simulation and rodent observations out of scope and retain the 2022 resource-currentness limitation. That limitation must remain visible in the eventual API/UI, not only in design prose.

## Review return criteria

All findings BND-001 through BND-008 are resolved. The OpenSpec CLI validation passed, and the source hash/shape/CRS claims were independently reproduced. Implementation must still provide the tests specified by the amended artifacts; this planning review does not authorize or verify implementation. `verification/gate.json` was not created by this review; the orchestrator must record the PASS decision and finding IDs there before the quality gate.
