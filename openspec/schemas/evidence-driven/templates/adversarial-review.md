# Adversarial Review

<!-- Planning artifact, written BEFORE tasks.md, by a reviewer context that did
     not author the proposal, specs, or design. Record the review as performed;
     never backfill it after implementation. Fields and tables below are read by
     python3 scripts/openspec_quality_gate.py <change>, which fails the change on
     a missing field, a placeholder value, an inconsistent blocking-finding
     count, or an unresolved BLOCKING finding.

     Runtime note: the independence mechanism is an observable property of the
     review, not a runtime requirement. Any execution environment that provides a
     separate reviewer context counts, and no runtime name, session id, or
     orchestration API is required - runtime identifiers are optional provenance. -->

## Review Record

- Change: <change-name>
- Review type: ADVERSARIAL_REVIEW
- Reviewer (agent/session and role):
- Author context (agent/session that wrote proposal/specs/design):
- Independence mechanism: SEPARATE_SESSION | SEPARATE_WORKTREE | SEPARATE_AGENT | SEPARATE_MODEL | HUMAN | NONE
- Independence exception reason (required when the mechanism is NONE):
- Independence waiver (human decision reference, required when the mechanism is NONE):
- Artifacts reviewed (paths):
- Reviewed at (UTC): <YYYY-MM-DDThh:mm:ssZ>

## Review Scope

Mark every area `Reviewed` or `Not applicable - <reason>`. An area marked
`Reviewed` with no finding is a claim that you challenged it, not that you read it.

- Requirements:
- Architecture:
- Scientific assumptions:
- Evidence quality:
- Acceptance criteria:
- Failure scenarios:

## Assumption Challenges

<!-- For each assumption the proposal, specs, or design depends on: state the
     assumption, what it rests on, what breaks if it is wrong, and whether the
     artifact supports it. Cite artifact paths and sections. -->

## Requirement Gaps

<!-- Missing, ambiguous, contradictory, or untestable requirements. Name the gap
     and the artifact/section it belongs to; "none found" is only credible next
     to the requirement list you checked. -->

## Design Counterexamples

<!-- Concrete scenarios in which the proposed design fails: inputs, state,
     timing, failure mode, and the observable consequence. Prefer a scenario a
     test could reproduce over a generic risk. -->

## Scientific Validity

Address each item. Unknown values stay unknown; never invent a value, citation,
parameter, or confidence score to close a challenge.

- Evidence applicability:
- Biological assumptions:
- Parameter provenance:
- Mathematical assumptions:
- Model limitations:
- Falsifiability:
- Uncertainty:

## Acceptance Criteria Weaknesses

<!-- Requirements that cannot be independently verified: what would have to be
     observable to verify them, and what is missing. -->

## Findings

<!-- One row per finding. Severity: BLOCKING | MAJOR | MINOR | INFO.
     Status: OPEN | RESOLVED | ACCEPTED_RISK | DEFERRED.
     "Evidence or reasoning" must be checkable (path, section, command, or
     calculation); "Proposed resolution" must be actionable. A BLOCKING finding
     may only be closed as ACCEPTED_RISK with a recorded human decision
     reference. -->

| Finding ID | Severity | Affected artifact | Evidence or reasoning | Proposed resolution | Status |
| ---------- | -------- | ----------------- | --------------------- | ------------------- | ------ |
| AR-1 | BLOCKING | specs/<capability>/spec.md - Requirement: <name> | <evidence, path, or reasoning> | <resolution> | RESOLVED |

## Review Decision

Decision: PASS | PASS_WITH_WARNINGS | BLOCKED

- Blocking findings open: <integer, must equal the BLOCKING rows above that are not RESOLVED>
- Basis for the decision:
- Required resolutions before tasks.md:
- If BLOCKED, resolution owner and next step:
