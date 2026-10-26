# Design

## Evidence boundary

Evidence → assumptions → model → validation remains mandatory. `OBSERVED`, `UNVERIFIED`, `INFERRED`, and `SIMULATED` remain distinct. Existing synthetic reports are not observations and cannot seed biological origins without a separately approved contract.

## Vertical integration shape

Reuse current layers: `packages/geo` owns CRS/network/features, `packages/simulation` owns origins/transitions/aggregation, FastAPI owns provenance/contracts, PostGIS owns versioned source data, and Next.js owns scenario configuration/explanation.

The first safe runtime remains surface-only OSM plus separately displayed stormwater reference geometry. Underground layers never become movement edges from geometric intersection or proximity.

## Approval gates before implementation

1. Written source authorization, license, retention/privacy, schema, CRS, stable IDs, hash, coverage, and currentness for each real source.
2. Public-health/modeler approval for report-to-origin semantics, species assumptions, transition weights, time interpretation, and validation targets.
3. Infrastructure confirmation for sewer topology and any cross-layer transfer.
4. Human decision on compatibility and scientific assumptions.

## Scenario contract

Baseline and environment-aware modes must differ through versioned, inspectable feature inputs and coefficients, not presentation-only overlays. Unknown coefficients remain hypothetical and dimensionless. Results expose contributing features, source versions, seed, model version, uncertainty, and limitations.
