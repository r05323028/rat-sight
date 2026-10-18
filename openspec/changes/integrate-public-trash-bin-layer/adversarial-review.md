# Adversarial review — public trash-bin feasibility

**Reviewer:** verification-reviewer  
**Decision:** PASS for the Phase A feasibility/research boundary. The implementation decision remains conditional NO-GO; this review does not authorize code or raw-source access.

## Scope and evidence reviewed

Reviewed `proposal.md`, `design.md`, `specs/public-trash-bins/spec.md`, `tasks.md`, `evidence.md`, `docs/evidence/public-trash-bin-feasibility-2026-10-18.md`, public infrastructure/public-health reviews, QA, traceability, and `openspec validate integrate-public-trash-bin-layer`.

No code or raw source files were accessed in this review.

## Findings

### TB-001 — HIGH / RESOLVED: feasibility decision was internally inconsistent

**Evidence:** `proposal.md` and `design.md` state conditional NO-GO for implementation because CRS/axis order is unresolved. `verification/qa.md` and both independent domain reviews also say implementation is blocked. However, the feasibility evidence headline says “GO” for a narrowly scoped reference layer, while its recommendation says “Proceed only” after CRS confirmation or a human-approved unknown-CRS contract.

**Impact:** A downstream implementer or gate reader could interpret the headline as implementation authorization despite the OpenSpec requirement for verified CRS and the explicit no-code boundary.

**Resolution verified:** The evidence headline and related artifacts now use conditional NO-GO for implementation. Feasibility/reference discussion is not build authorization.

### TB-002 — HIGH / RESOLVED: research quality-gate closure was incomplete

**Evidence:** `tasks.md` leaves verification task 8 unchecked; no `verification/gate.json` or `verification/code-review.md` exists. QA and traceability are present but explicitly describe feasibility/conditional NO-GO, and no quality-gate result records the adversarial/code review decisions.

**Impact:** The substantive evidence is strong, but the change is not yet independently gate-complete or Ready for Human Review under repository workflow.

**Resolution verified:** Docs-only `verification/code-review.md`, QA, traceability, and `verification/gate.json` are present. `make openspec-gate CHANGE=integrate-public-trash-bin-layer` passes. Implementation requirements remain NOT_APPLICABLE under conditional NO-GO.

### TB-003 — MEDIUM / RESOLVED: generated identity normalization was underspecified

**Evidence:** Design/evidence permit a generated identity from normalized source fields and warn that edits change identity, but do not define Unicode normalization, whitespace/encoding handling, field order, delimiter/escaping, numeric lexical normalization, or collision handling.

**Impact:** Future implementations could produce different IDs from the same source row or collide distinct rows, undermining idempotency and source traceability.

**Resolution verified:** The canonical generated-ID algorithm and collision/failure behavior are now recorded. Generated IDs remain technical and source-scoped, never official facility IDs.

### TB-004 — MEDIUM / RESOLVED: MVP resource selection and human decision were not recorded

**Evidence:** Resource A has 681 rows and one malformed coordinate; Resource B has 130 rows and is a tourist/commerce subset. The design says “one authoritative resource,” but no artifact selects A or B for a future MVP or records the human decision/coverage rationale.

**Impact:** An implementer could silently union or choose the smaller subset, creating incomplete or duplicated coverage claims.

**Resolution verified:** No MVP resource is selected; human selection is explicitly required before implementation. Resources A and B remain separate absent a publisher crosswalk, with resource-specific provenance and limitations preserved.

## Positive assessment

- Source IDs, resource IDs, URLs, hashes, CP950 encoding, schema, row counts, malformed/duplicate coordinate findings, and currentness limits are unusually well documented.
- Both independent domain reviews correctly reject CRS inference, coordinate repair, coordinate-based deduplication, resource union, and rodent/food/risk/simulation claims.
- The no-code/no-stored-raw-data boundary is explicit and supported by QA/traceability.
- The conditional implementation design preserves provenance, `UNVERIFIED` currentness, resource separation, strict malformed-coordinate handling, and public-cleanliness semantics.

## Return criteria

TB-001 through TB-004 are resolved. The recorded gate result is PASS from `make openspec-gate CHANGE=integrate-public-trash-bin-layer`. This PASS covers the feasibility/research artifacts only; no importer, migration, API, UI, spatial transformation, or raw-source implementation is authorized while the conditional NO-GO gates remain unresolved.
