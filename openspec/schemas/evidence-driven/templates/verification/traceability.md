# Traceability Validation

<!-- Post-implementation record. Maps the change's requirements to their
     evidence, and RatSight's scientific chain to its evidence, using stable
     identifiers. Fields and tables below are read by
     python3 scripts/openspec_quality_gate.py <change>.

     Requirement ID format (stable, derived from the delta spec, do not invent):
       <capability-path>#<requirement-heading-slug>
       <capability-path>#<requirement-heading-slug>/<scenario-heading-slug>
     The capability path is the spec file's directory under specs/, and a slug is
     the heading lowercased with runs of non-alphanumeric characters replaced by
     "-", e.g. specs/user-auth/spec.md "### Requirement: User can export data"
     becomes user-auth#user-can-export-data.

     Statuses: VERIFIED | PARTIALLY_VERIFIED | UNVERIFIED | NOT_APPLICABLE.
     UNVERIFIED blocks the gate: verify it, or record NOT_APPLICABLE with a
     reason. Data classes: OBSERVED | INFERRED | SIMULATED | UNVERIFIED. -->

## Traceability Record

- Change: <change-name>
- Traceability reviewer (agent/session and role):
- Independence mechanism: SEPARATE_SESSION | SEPARATE_WORKTREE | SEPARATE_AGENT | SEPARATE_MODEL | HUMAN | NONE
- Independence exception reason (required when the mechanism is NONE):
- Verified at (UTC): <YYYY-MM-DDThh:mm:ssZ>
- Scientific Traceability Applicability: APPLICABLE | NOT_APPLICABLE
- Non-applicability reason (required when NOT_APPLICABLE, e.g. "tooling-only change, no scientific claim or parameter"):

## Execution Evidence

<!-- Every command relied on as verification evidence. Exit code must be 0 for
     any row cited as executed evidence. Record what was actually run: an
     unexecuted test, a checked box, or an agent's success report is not
     evidence. -->

| Command | Exit code | Result summary | Recorded by |
| ------- | --------- | -------------- | ----------- |
| `make test-py` | 0 | 12 passed | <agent/session and timestamp> |

## Engineering Traceability

<!-- One row per requirement in the change's delta specs; list every scenario of
     that requirement in the Acceptance Criteria / Scenario cell. Requirement
     IDs must match the specs under specs/ exactly, and are checked for coverage:
     a requirement with no row fails the gate.

     VERIFIED requires Implementation, Tests, and an Execution Evidence command
     recorded above. PARTIALLY_VERIFIED and NOT_APPLICABLE require a reason in
     Residual gaps. -->

| Requirement ID | Acceptance Criteria / Scenario | Implementation | Tests | Execution Evidence (command) | Status | Residual gaps |
| -------------- | ------------------------------ | -------------- | ----- | ---------------------------- | ------ | ------------- |
| <capability>#<requirement-slug> | <capability>#<requirement-slug>/<scenario-slug> | <path:symbol> | <test path/test name> | `make test-py` | VERIFIED | None. |

## Unplanned or Deviations

<!-- Behavior that shipped but was not in the specs, or spec behavior that was
     implemented differently. Rows are reviewed by someone other than the
     implementer. When there is none, keep the single line "- None." -->

| Deviation ID | Description | Spec impact | Reviewed by | Decision |
| ------------ | ----------- | ----------- | ----------- | -------- |

- None.

## QA and Model Validation

- QA owner (agent/session):
- Test suites executed: <commands, matching the Execution Evidence table>
- Scientific model validation: <validation record path under docs/evidence/, or "Not applicable - <reason>">

## Scientific Traceability

<!-- Required when Scientific Traceability Applicability is APPLICABLE.
     Chain: research evidence -> scientific assumption -> model parameter ->
     mathematical model -> validation evidence.

     Evidence IDs must resolve to a record under docs/evidence/ (not to a
     template, blog post, or memory). A row whose Data class is SIMULATED must
     not describe observed migration, routes, movement, or counts: simulated
     output is not an observation. Parameter values that are unknown stay
     "unknown" - never substituted with a plausible number. -->

| Evidence ID | Scientific Assumption | Parameter ID | Mathematical Model | Validation Evidence | Data class | Status | Residual gaps / uncertainty |
| ----------- | --------------------- | ------------ | ------------------ | ------------------- | ---------- | ------ | --------------------------- |
| <EVIDENCE-ID from docs/evidence/> | <assumption> | <PARAM-ID or "unknown"> | <model and version> | <command or docs/evidence/ path> | INFERRED | VERIFIED | <limits and uncertainty> |

## Traceability Decision

Decision: VERIFIED | PARTIALLY_VERIFIED | UNVERIFIED | NOT_APPLICABLE

- Unverified requirements remaining: <integer, must equal the rows marked UNVERIFIED>
- Basis for the decision:
