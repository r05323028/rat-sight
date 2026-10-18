# Proposal

## Why

RatSight needs a verified environmental reference layer for Taipei public trash bins. The layer will support facility visualization and inspection only; it is not rodent evidence or a risk factor.

## Current feasibility decision

**CONDITIONAL NO-GO for implementation.** The official resources and point-like values are documented, but publisher CRS/axis order is absent; WGS84-looking coordinates are only an inference. No importer, migration, API, UI, or spatial transformation is authorized until the publisher confirms CRS/axis order or the human-approved contract explicitly supports unknown CRS without assigning EPSG:4326.

## What Changes

- Record verified dataset/resource metadata, hashes, schemas, encoding, coordinate quality, identity, overlap, and currentness.
- Complete the feasibility/reference review and preserve the exact implementation blockers.
- Do not build the vertical slice unless the CRS/identity/reuse gate is later approved; this change stops at a documented conditional NO-GO.

## Integrity Boundary

Records remain public-cleanliness infrastructure reference data with explicit provenance and uncertainty. They must remain separate from rodent reports, simulation, population, infestation, movement, disease risk, and causal claims.
