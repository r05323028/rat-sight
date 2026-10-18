# Independent QA — integrate-public-trash-bin-layer

**Verdict: CLEAR for Phase A feasibility; conditional NO-GO for implementation.**

## Evidence

- `openspec validate integrate-public-trash-bin-layer`: PASS / valid.
- `docs/evidence/public-trash-bin-feasibility-2026-10-18.md`: records official dataset/resource IDs, URLs, license, CP950 schemas, exact bytes and SHA-256, row counts, malformed/duplicate coordinates, resource separation, currentness, and CRS uncertainty.
- Independent infrastructure review: `verification/public-infrastructure-review.md` confirms CRS/axis order is unresolved and requires strict coordinate/identity/resource rules.
- Independent public-health review: `verification/public-health-review.md` confirms environmental reference semantics and rejects rodent/food/risk inference.
- No code/data implementation: no importer, migration, API, UI, dependency, or stored raw CSV changes. Temporary official files were deleted and are not in Git.

## Decision

The evidence supports a narrowly scoped public-cleanliness facility reference proposal, but not implementation under the current contract. Publisher CRS/axis order must be confirmed or a human-approved unknown-CRS contract must explicitly prohibit EPSG:4326 assignment/transformation. Resource A and B must remain separate; malformed coordinates must be rejected/quarantined; generated identities must not be called official IDs; currentness remains `UNVERIFIED`.

The layer must never be represented as rodent observations, food availability, infestation, movement, risk, causal evidence, or simulation input.

## Limitations

No vertical-slice smoke, importer, API, or browser tests were run because the feasibility gate failed before implementation. Existing layer behavior is unchanged by this change. No human project-owner acceptance is claimed.
