# Public infrastructure review: Taipei trash-bin feasibility

**Review date:** 2026-10-18 (Asia/Taipei)  
**Artifact reviewed:** `docs/evidence/public-trash-bin-feasibility-2026-10-18.md`  
**Boundary:** independent infrastructure/data-quality review only; no raw source files, database, application code, or external records accessed.

## Decision

**GO for a narrowly scoped feasibility/reference proposal; NO-GO for implementation until the conditions below are satisfied.** The evidence supports an official public-cleanliness facility candidate, not rodent evidence, infrastructure connectivity, food availability, risk, or causal intervention data. The OpenSpec requirement for a *verified* CRS and source contract is not currently met: the publisher-declared CRS/axis order is absent from the inspected metadata, and WGS84-looking coordinates are only an inference.

## Review findings

| Check | Status | Finding and consequence |
|---|---|---|
| Source identity | VERIFIED | Dataset `a835f3ba-7f50-4b0d-91a6-9df128632d1c` is identified as `臺北市行人專用清潔箱`, provided by Taipei City Environmental Protection Department. Resources A and B have distinct resource IDs and URLs. |
| License/attribution | PARTIALLY VERIFIED | Portal reports `公開` and links Government Data Open License terms. The implementation must retain the exact license/attribution record and must not treat portal availability as proof of unrestricted use beyond those terms. |
| Resource relationship | VERIFIED | A is the general public-cleaning-bin table; B is explicitly a 130-point tourist/commerce subset. They must remain separate unless a publisher crosswalk authorizes merging. |
| Encoding/schema | VERIFIED | Both are CP950/Big5 CSVs with the same five fields: `行政區`, `地址`, `經度`, `緯度`, `備註`. Encoding must be explicit in provenance and importer behavior. |
| Geometry representation | PARTIALLY VERIFIED | Evidence reports finite point-like coordinate pairs, but no geometry file/CRS declaration was established. Coordinates must not be silently assigned EPSG:4326. |
| Geometry quality | CONDITIONAL | A has one malformed longitude (`?121.595369`) and 680 parseable rows within the check envelope; B has no malformed coordinates under the stated check. Any importer must reject/quarantine malformed A rows and report counts. |
| Identity/duplicates | CONDITIONAL | Neither resource has a stable publisher row ID, version, or verification date. A has one exact coordinate duplicate; B has ten. Full rows are unique, but coordinate pairs are not identity. A generated source-scoped identity from normalized full source-row content is acceptable only if documented as generated and its edit-instability is retained. |
| Cross-resource overlap | VERIFIED only for exact comparisons | Evidence found zero exact overlap for coordinate, address, and `(行政區, 地址)` comparisons. This does not prove geographic non-overlap after normalization/rounding; never union A/B by coordinate proximity without an approved crosswalk. |
| Currentness | UNVERIFIED | Catalog collection ends 2018-01-10 while metadata/resources were updated in 2026. Update timestamps do not prove field survey or location currency. Currentness must be visible as `UNVERIFIED`. |
| Semantics | VERIFIED as environmental reference only | These are public cleaning-bin locations. No evidence supports claims about rodent abundance, food availability, movement, infestation, or intervention effects. |

## Required GO conditions before implementation

1. Obtain publisher confirmation of CRS and axis order, or explicitly revise the contract to support an `unknown` CRS state and prohibit spatial import/transformation until confirmation. A value that merely resembles WGS84 is not sufficient.
2. Preserve each resource separately with dataset/resource IDs, canonical/download URLs, retrieval timestamp, byte count and SHA-256, CP950 encoding, publisher, license/attribution, source version/update timestamps, and `classification=UNVERIFIED` for currentness/coordinate uncertainty.
3. Define and test strict coordinate validation: reject/quarantine non-numeric values such as `?121.595369`, non-finite/out-of-envelope values, and axis reversals; publish rejection counts. Do not silently strip prefixes or repair coordinates.
4. Define source-scoped generated identity from normalized source fields only if no official ID is supplied; retain raw fields and state that edits can create a new identity. Do not use coordinates as identity or deduplicate B's repeated coordinates.
5. Keep A and B as distinct resources/layers. Any merge or overlap assertion requires publisher crosswalk or an explicitly approved normalization method.
6. Keep `data_class` as public-cleanliness/environmental reference and keep it separate from `OBSERVED`, `INFERRED`, `SIMULATED`, and rodent-report data. UI/API text must state that bins are not a rodent proxy.
7. Complete privacy/access review for exact addresses and points, and avoid joins with citizen reports. The evidence found no personal fields, but location precision can still enable facility targeting.

## Explicit NO-GO boundaries

- No importer, migration, API, UI, simulation input, risk score, movement weight, or rodent inference should be implemented while CRS/axis order remains unresolved under the current OpenSpec contract.
- Do not merge the two resources, deduplicate repeated coordinates, infer missing facilities, or claim coverage/completeness from the catalog.
- Do not label the layer `OBSERVED` rodent data or interpret a bin as food availability, infestation, or causal intervention evidence.

## Review conclusion

The feasibility evidence is sufficient to proceed to a human/source-owner decision for a reference-only layer, but not sufficient to authorize implementation under the current verified-source requirement. The recommended gate is **GO for proposal and authorization; conditional NO-GO for build** until CRS/axis order and the resource-level reuse/attribution record are confirmed and the quality/identity rules above are accepted.
