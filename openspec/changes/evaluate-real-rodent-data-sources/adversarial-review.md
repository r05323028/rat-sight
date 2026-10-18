# Adversarial review — evaluate real rodent data sources

**Reviewer:** verification-reviewer

**Decision:** PASS for the research-only feasibility scope; real-source work remains NO-GO pending human authorization.

## Scope and evidence reviewed

Reviewed `proposal.md`, `design.md`, `specs/real-rodent-data-sources/spec.md`, the existing source investigation `docs/evidence/rodent-report-source-investigation-2026-10-17.md`, and `docs/evidence/rodent-report-acceptance-2026-10-17.md`.

The existing source investigation is appropriately conservative: it did not download citizen records, keeps Rat Radar/Taipei open-data/1999 candidates `UNVERIFIED`, distinguishes reports from observations, and identifies licensing/privacy/CRS/coverage blockers. The fixture acceptance report also explicitly says real-source integration remains blocked.

## Findings

### RDS-001 — BLOCKING / HIGH / RESOLVED: OpenSpec validation failed because the delta header was missing

**Resolution verified:** The spec now uses `## ADDED Requirements` with scenarios, and `openspec validate evaluate-real-rodent-data-sources` passes (with no validation errors).

### RDS-002 — HIGH / RESOLVED: no new evidence-comparison artifact or claim-level traceability was present

**Resolution verified:** `verification/source-comparison.md` now provides claim IDs, URLs, verification date, status, semantics, limitations, and source-boundary consequences for Rat Radar, Taipei open-data, Taipei 1999, and other official candidates.

### RDS-003 — HIGH / RESOLVED: current recommendation and human decision request were conditional rather than explicit

**Resolution verified:** `proposal.md`, `evidence.md`, and `recommendation.md` explicitly state `NO-GO` for real download, ingestion, redistribution, and model use for every candidate. They name the human project owner via the supported OpenRig gateway/queue and limit any possible authorization to a bounded metadata/data-owner clarification step.

### RDS-004 — MEDIUM / RESOLVED: proposed next implementation contract was not concrete enough for a future gate

**Resolution verified:** `design.md` now contains an explicit unknown-blocks-implementation checklist covering source identity/access, permission, fields/forbidden data, semantics, spatial and temporal precision, validation/provenance, retention/update behavior, API exposure, and failure states.

### RDS-005 — MEDIUM / RESOLVED: no task/evidence lifecycle was defined for this research change

**Resolution verified:** `tasks.md` now defines an evidence lifecycle, independent public-health/privacy review, explicit NO-GO recommendation, human decision gate, independent adversarial review, validation/quality-gate evidence, and a final no-download/no-ingestion boundary. No implementation tasks were added.

## Positive assessment

- The prior investigation preserves `UNVERIFIED` status and does not manufacture source access, licensing, privacy, CRS, coverage, or scientific claims.
- The design correctly treats public visibility as distinct from permission to reuse and keeps reports separate from observations, treatment, prevalence, and causal evidence.
- The proposal explicitly prohibits raw citizen records, photos, names, exact addresses, and exact coordinates.

## Return criteria

RDS-001 through RDS-005 are resolved. The research-only feasibility review is **PASS** and the change is ready for human review. The explicit current decision remains **NO-GO** for real download, ingestion, redistribution, and model use; human authorization is still required before any bounded metadata contact step, and no real records may be accessed under this change.
