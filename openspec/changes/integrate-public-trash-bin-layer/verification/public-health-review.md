# Public-health review — public trash-bin reference layer

**Review date:** 2026-10-18  
**Review boundary:** Independent review of `docs/evidence/public-trash-bin-feasibility-2026-10-18.md` and the active proposal/design/spec/tasks. No additional raw-data access and no code changes.  
**Decision:** **CONDITIONAL GO only as a public-cleanliness reference layer; NO-GO for rodent, food-availability, infestation, movement, risk, or causal use. Implementation remains gated on essential source verification.**

## Evidence reviewed

The feasibility artifact identifies Taipei City Data Platform dataset `a835f3ba-7f50-4b0d-91a6-9df128632d1c`, provider Taipei City Environmental Protection Department, and two distinct resources:

- Resource A `267d550f-c6ec-46e0-b8af-fd5a464eb098`: 681 rows, one malformed longitude, one exact coordinate duplicate, 2018 collection end metadata.
- Resource B `2030d728-9597-437d-81a4-cf2a44c7f114`: 130 rows, ten duplicate coordinate pairs, explicitly a tourist/commerce subset.

The artifact records temporary downloads deleted after analysis, CP950/Big5 encoding, portal Government Data Open License metadata, source hashes, and URLs. Those facts support a narrowly bounded reference-layer assessment, not biological or currentness claims.

## Findings

### 1. Scientific semantics — suitable only as facility reference

A public cleaning-bin point indicates a publisher-listed amenity/facility location. It does not measure:

- rodent sightings, abundance, occupancy, or infestation;
- food availability, waste volume, sanitation condition, or attractant presence;
- animal movement, corridor connectivity, or movement weights;
- disease risk or intervention effectiveness.

The proposal/design/spec correctly isolate the layer from rodent reports, simulation, population, risk, and causal claims. UI, API descriptions, legend text, and selection details must retain this boundary. Avoid labels such as “rodent habitat,” “food source,” “risk factor,” “hotspot,” “infestation,” or “priority intervention” for this layer.

### 2. Currentness — material limitation and user-facing requirement

The catalog collection end date is 2018-01-10 while resources/metadata were updated in 2026. A resource update timestamp does not establish that each facility was surveyed, remains installed, or is operational. The layer must visibly state that currentness is `UNVERIFIED`, preserve collection and resource dates separately, and avoid “current bins” or complete coverage language.

The source's “update” metadata must not be interpreted as field verification. Any operational inspection use requires a separate field-verification process and date.

### 3. Spatial/CRS — implementation blocker until resolved

Coordinates appear plausible as longitude/latitude, but source CRS and axis order are not declared in the reviewed evidence. The system must not silently label geometry EPSG:4326 or expose spatial accuracy claims. Confirm CRS with the publisher or retain the layer as unavailable/blocked; a check envelope is a validation guard, not CRS evidence.

Resource A's `?121.595369` must fail or be quarantined with a visible quality count; stripping the prefix would fabricate a clean coordinate. Resource B's repeated coordinates must not be deduplicated without a publisher rule because multiple bins may share/round to a coordinate.

### 4. Resource separation and identity

Resource B is explicitly a 130-point tourist/commerce subset and must not be unioned with Resource A merely because schemas resemble each other. Separate resource identity, coverage, hashes, retrieval dates, and limitations are required. A generated source identity is acceptable only as a source-scoped technical key and must never be presented as an official facility ID.

Neither coordinate nor address uniqueness is established as a stable facility identity. Source edits can change a generated content identity; update behavior must remain explicit.

### 5. Privacy and public exposure

No personal fields were observed, but exact addresses and point coordinates can facilitate physical targeting or reveal facility context. Public-data licensing does not remove the need for minimization, access review, attribution, and avoidance of joins with citizen reports or sensitive datasets. Do not expose raw source notes if they contain unreviewed free text; the approved field allowlist must be explicit.

The layer should provide source/resource attribution, retrieval date, currentness limitation, CRS status, and quality flags. It must not enable an inference that nearby complaints or rodent reports establish a causal relationship.

## Required UI/API language

At minimum, display:

> Public cleaning-bin reference locations from the cited Taipei source. Source CRS and currentness may be unverified; collection/resource dates are shown separately. These points are not rodent observations, food-availability measurements, infestation or risk indicators, movement routes, or evidence of intervention benefit.

Selection details should use “publisher-listed public cleaning bin” and show source/resource identity, not “observed facility” or “verified current facility.” If CRS is unresolved, do not render a map layer as if its positional accuracy were established.

## Required exclusions

- No rodent, pest, sanitation, food, disease, infestation, prevalence, risk, hotspot, or causal claims.
- No movement graph edges, movement weights, model parameters, simulation inputs, or intervention prioritization.
- No silent CRS/EPSG:4326 assumption or coordinate cleanup.
- No union of Resource A and B without a source-owner relationship/crosswalk.
- No deduplication from coordinate equality alone.
- No claim of currentness, completeness, operational status, or field verification from 2026 metadata timestamps.
- No joins to citizen reports, complaint records, or other sensitive data that could create unsupported or privacy-sensitive inferences.

## Conditional GO criteria

A future implementation may proceed only after:

1. publisher/source relationship and applicable license/attribution terms are recorded;
2. CRS and axis order are confirmed, or the layer remains blocked/unavailable;
3. one MVP resource is selected with explicit coverage rationale; Resource A and B remain separate otherwise;
4. malformed coordinates are rejected/quarantined and duplicate policy is documented;
5. generated IDs are clearly marked technical and source-scoped;
6. currentness, collection period, retrieval date, and uncertainty are shown in API/UI;
7. public-health/infrastructure review confirms the no-biological-claims wording.

## Conclusion

The feasibility artifact's narrow administrative/public-amenity GO is scientifically appropriate, provided it is not treated as evidence about rodents or environmental risk. Because CRS is still unverified and currentness is materially limited, this review does not authorize implementation until the conditional gates are satisfied. No raw data were accessed in this review.
