# Independent Code Review

<!-- Post-implementation record. Written from a reviewer context separate from
     the implementer, against the actual diff and the connected code - not the
     implementer's summary. Fields and tables below are read by
     python3 scripts/openspec_quality_gate.py <change>, which fails the change on
     self-review, a missing field, a placeholder value, an inconsistent
     blocking-finding count, an unresolved BLOCKING finding, or a resolved
     finding with no recorded re-verification.

     Runtime note: independence is an observable property of the review, not a
     runtime requirement. Any execution environment that provides a separate
     reviewer context counts, and no runtime name, session id, or orchestration
     API is required - runtime identifiers are optional provenance. -->

## Review Record

- Change: <change-name>
- Review type: INDEPENDENT_CODE_REVIEW
- Reviewer (agent/session and role):
- Implementer (agent/session):
- Independence mechanism: SEPARATE_SESSION | SEPARATE_WORKTREE | SEPARATE_AGENT | SEPARATE_MODEL | HUMAN | NONE
- Independence exception reason (required when the mechanism is NONE):
- Independence waiver (human decision reference, required when the mechanism is NONE):
- Verification of independence: <how someone else can check this claim: distinct session id, worktree path, different agent/model, or human>
- Diff reviewed (base..head, commit, or worktree state):
- Coverage (files and areas inspected, including connected code):
- Implementation summary relied on (optional):
- Reviewed at (UTC): <YYYY-MM-DDThh:mm:ssZ>

## Review Method

Confirm what was inspected in the source, not what the implementer reported.
Mark each area `Reviewed`, `Reviewed - no issues found`, or
`Not applicable - <reason>`.

- Actual code changes:
- Relevant surrounding code:
- Specifications:
- Design decisions:
- Tests:
- Error handling:
- Security implications:
- Regression risks:

## Findings

<!-- One row per finding. Severity: BLOCKING | MAJOR | MINOR | INFO.
     Status: OPEN | RESOLVED | ACCEPTED_RISK | DEFERRED.
     "File and location" must name a path with line, symbol, or section.
     "Reproduction or supporting evidence" must be checkable. A BLOCKING finding
     may only be closed as ACCEPTED_RISK with a recorded human decision
     reference. Every RESOLVED finding needs a Follow-up Verification row. -->

| Finding ID | Severity | File and location | Description | Reproduction or supporting evidence | Recommended correction | Status |
| ---------- | -------- | ----------------- | ----------- | ----------------------------------- | ---------------------- | ------ |
| CR-1 | BLOCKING | <path>:<line> | <defect> | <command output, test, or reasoning> | <correction> | RESOLVED |

## Follow-up Verification

<!-- Required when any finding is RESOLVED: record the re-check, not the claim
     that it was fixed. One row per resolved finding. -->

| Finding ID | Re-verification command or check | Result |
| ---------- | -------------------------------- | ------ |
| CR-1 | <command or inspection> | <observed result> |

## Review Decision

Decision: PASS | PASS_WITH_WARNINGS | BLOCKED

- Blocking findings open: <integer, must equal the BLOCKING rows above that are not RESOLVED>
- Basis for the decision:
- Residual risk accepted:
