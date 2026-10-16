# Adversarial Review

**Decision: PASS**

`openspec validate integrate-taipei-stormwater-network` passes with three long-requirement warnings. Candidate B is a reasonable source candidate and the proposal correctly keeps infrastructure separate from rodent/simulation claims. The amendments resolve the identity, provenance, dimensional CRS, bbox, official-check command, broad-scope, source-key evidence, and public segment-identifier concerns. The planning artifacts are ready for tasks.

## Findings

### SW-001 — BLOCKING / HIGH / RESOLVED: provenance was named but not typed as an implementable contract

**Resolution verified:** `spec.md` now defines the exact top-level and nested `StormwaterProvenanceV1` keys, types/formats, required values, top-level ownership, and immutable serialization. `design.md` aligns backend ownership/immutability and includes source/download URLs, license, CRS, processing, reference-only/data-quality fields, and uncertainty.

### SW-002 — BLOCKING / HIGH / RESOLVED: deterministic source identity and idempotency were contradictory

**Resolution verified:** The amended design/spec select unique normalized source `識別碼` as `source_record_id`, keep duplicate/missing `管線編號` as nullable non-key attributes, use `(dataset_id, resource_version, source_record_id)` as the unique key, compare content hashes on re-import, fail closed on changed content or omitted records, and forbid topology inference. The remaining need is implementation/evidence testing.

### SW-003 — HIGH / RESOLVED: 3D geometry and vertical-coordinate semantics were unresolved

**Resolution verified:** The amended design/spec require homogeneous 3D input, drop unresolved Z to 2D EPSG:4326, record the unresolved vertical datum in provenance, and reject unsupported/mixed dimensions.

### SW-004 — HIGH / RESOLVED: bounded bbox contract and frontend query lifecycle were underspecified

**Resolution verified:** The amended spec defines finite EPSG:4326 ranges/order, maximum 0.30-degree width/height, HTTP 422 for invalid input, selected-version contract, feature-count/bbox echo, and 5,000-feature truncation. The design defines initial and debounced `moveend` viewport requests, partial-result messaging, and stale-layer removal/error handling.

### SW-005 — HIGH / RESOLVED: one-time official district verification lacked a reproducible command

**Resolution verified:** The amended design/spec name `scripts/verify_official_districts.sh`, temporary isolated database/archive cleanup, source hash, importer/API/dashboard assertions, `apps/web/e2e/official-district.spec.ts`, durable OpenSpec QA recording, and non-regular-test scope.

### SW-006 — MEDIUM / RESOLVED: the source-attribute allowlist was not enumerated

**Resolution verified:** `design.md` now enumerates the exact feature-property allowlist, nullable types, and `Unavailable` rendering. It explicitly labels `start_node_id`/`end_node_id` as publisher attributes and not verified connectivity.

## Positive assessment

- Candidate B is better justified than Candidate A for an MVP because its horizontal CRS is explicitly declared and its publisher reference-only warning is preserved.
- The proposal explicitly excludes topology inference, rodent claims, synchronization, generic ETL, and simulation integration.
- The requested dedicated table/API/layer and archive-only approach are proportionate, provided identity and bounded-query contracts are made deterministic.

### SW-007 — MEDIUM / RESOLVED: evidence did not establish `識別碼` completeness/uniqueness

**Resolution verified:** The evidence now records all 19,747 `識別碼` values as non-empty and unique, and the contract requires normalized unique values with fail-closed missing/duplicate handling. The source-key evidence is now aligned with the proposed persistence identity.

### SW-008 — HIGH / RESOLVED: design and spec disagreed on the public segment identifier property

**Resolution verified:** `design.md` now defines the public allowlist with opaque `segment_id` and explicitly states that persistence-only `source_record_id` is not exposed. This matches the exact public-property contract in `spec.md`.

## Return criteria

SW-001 through SW-008 are resolved by the amendments. The planning review is PASS and tasks may proceed. Implementation and one-time official verification remain future evidence; they must not be represented as run until executed. No implementation was edited. `verification/gate.json` was not created; the orchestrator must record this PASS decision and finding states before the quality gate.
