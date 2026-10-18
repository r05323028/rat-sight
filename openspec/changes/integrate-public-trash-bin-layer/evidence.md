# Feasibility decision

Verification date: 2026-10-18. Detailed evidence: `docs/evidence/public-trash-bin-feasibility-2026-10-18.md`.

## Verified

- Official dataset `a835f3ba-7f50-4b0d-91a6-9df128632d1c`, Taipei Environmental Protection Department, Government Data Open License terms and attribution requirement.
- Resource A `267d550f-c6ec-46e0-b8af-fd5a464eb098`: 63,540 bytes, SHA-256 `ff3cf5528c057958f89871aa5300fc633b02d0f7b37131ab29d5ddc2f8e2370d`, 681 rows, CP950 CSV, one malformed longitude and one duplicate coordinate.
- Resource B `2030d728-9597-437d-81a4-cf2a44c7f114`: 5,396 bytes, SHA-256 `47b1ddfb4f0ab4d5e57afab538f71da3d41d22e59c984bdd9c10b4248223b066`, 130 rows, CP950 CSV, ten duplicate coordinates.
- Both schemas are `行政區`, `地址`, `經度`, `緯度`, `備註`; no official row identifier, CRS declaration, or verification date exists.
- Resources are distinct tables; B is explicitly a 130-point tourist/commerce subset. Exact coordinate/address comparisons found no overlap, but normalized geographic overlap is unverified.

## Blockers

- Publisher CRS and axis order are absent. Coordinate values look WGS84-like but this is not sufficient to assign EPSG:4326 or transform.
- Generated source-scoped identity would be edit-sensitive and must not be presented as an official facility ID.
- Collection ends 2018 while metadata/resources were updated in 2026; currentness is `UNVERIFIED`.

## Decision

**Conditional NO-GO for implementation.** Phase A supports discussing a reference proposal, but no MVP resource is selected and no build is authorized. Proceed only after publisher CRS/axis confirmation or an explicitly human-approved unknown-CRS contract that forbids spatial import/transformation, plus accepted identity, resource-separation, strict malformed-coordinate, attribution/license, and privacy rules. Resource A and B remain separate; the human project owner must select one or explicitly retain both as separate future resources. The layer is environmental public-cleanliness reference data only—not rodent evidence, food availability, infestation, risk, movement, or simulation input.
