# Adversarial review

**Decision: PASS with implementation gates.**

### AR-FLD-001 — MAJOR — persistent volume ownership

A default command must not reuse `infra/docker-compose.yml`'s shared project/volume or delete unrelated resources. The implementation must use a distinct project name, explicit volume, free-port checks, and recorded-child cleanup. Human approval is required if ownership cannot be established.

**Resolution required in implementation:** prove project/volume names and teardown commands with tests and QA evidence.

### AR-FLD-002 — MAJOR — source mismatch or silent replacement

Official archives are pinned by documented SHA-256 and importer identity. Bootstrap must fail closed before writes on mismatch, missing files, CRS/format errors, or changed source records. It must not silently fetch a replacement or overwrite an existing version.

**Resolution required in implementation:** inspect-only and mismatch tests; preserve existing importer transactions.

### AR-FLD-003 — MAJOR — false completeness/scientific inference

Counts of 12 districts and 19,747 stormwater records describe the pinned source records only. They do not establish currentness, completeness, connectivity, traversability, rodent movement, risk, or intervention effect. UI and inventory must retain `UNVERIFIED` and reference-only limits.

**Resolution required in implementation:** inventory/provenance assertions and scientific review.

### AR-FLD-004 — MEDIUM — synthetic fixture accidentally enabled

The fixture importer is immutable and `SIMULATED`; default full-local bootstrap must not load it. Explicit opt-in must be visible in command output and UI.

**Resolution required in implementation:** default/opt-in tests.

### AR-FLD-005 — MEDIUM — candidate layer scope creep

Sewer, manhole, and trash-bin sources have unresolved or separate acceptance conditions. Assessment may recommend a next layer, but this change must not ingest or infer from them.

**Resolution required in implementation:** candidate assessment artifact and explicit no-go evidence.

### AR-FLD-006 — MAJOR — cross-source preflight/rollback — RESOLVED

The prior design did not prove whole-bootstrap safety for sequential imports. `design.md:13-15` now requires inspect-only preflight of both pinned sources before any import writes, and specifies that unexpected post-first-write failure reports no complete inventory. `spec.md:23-29` adds mismatch-before-write and post-first-write failure scenarios, including discard/recreate of the owned environment without affecting shared resources.

**Implementation gate:** verify both scenarios and record ownership-safe cleanup evidence before human review.
