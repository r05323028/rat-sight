# Strengthen OpenSpec verification and acceptance gates

> **Retrospective record.** This change documents work that was implemented before the record was
> written. No pre-implementation preflight approval exists for it, and none is claimed. The
> adversarial and code reviews it cites happened after implementation, as an independent acceptance
> review of the uncommitted work. Evidence is limited to what that review ran and to the regression
> tests added by the remediation.

## Why

The evidence-driven OpenSpec workflow could report success without verifying anything. An
acceptance review of the workflow itself found three blocking bypasses:

- A new change could declare `schema_version: 2` and be judged by the lax legacy rules, skipping
  the v3 finding, traceability, and evidence checks.
- CI validated zero changes and exited 0 whenever the diff base was unresolvable, which a default
  shallow checkout made the normal case, so a green check proved nothing.
- Task counting recognised only `[ ]`, `[x]`, and `[X]`: a `[~]` or `[-]` checklist item
  disappeared from the count, letting unfinished work pass as complete.

Four further weaknesses were recorded as moderate or minor: evidence references needed only to
resolve to some file (including the agent's own verification prose), `--skip-openspec` demoted
requirement coverage to warnings at readiness, the project schema had silently replaced an upstream
apply instruction instead of appending to it, and the review-workflow benchmark reported numbers as
if they were measured precision. The review also accepted limitations: task deletion cannot be
detected, and vacuous tests still count as verification.

## What Changes

- Freeze legacy record version 2 to the sixteen change records that already existed. Every other
  change that declares version 2 is rejected and evaluated under the current checks; legacy changes
  may opt in by declaring version 3.
- Resolve the CI diff base from the event (pull-request base, push `before`, or the default branch),
  fail when it cannot resolve, fail when it resolves to HEAD, and report a legitimately empty change
  set as empty rather than as validation success.
- Count every checkbox marker. Only `[x]` and `[X]` complete a task; other markers stay unfinished
  and raise a warning from the same parser used by the gate and the acceptance CLI.
- Replace the template's default reference to agent-authored QA prose with a CI artifact
  placeholder, and state that a reference is a pointer, not proof of correctness.
- Make `--skip-openspec` planning-only: at readiness, skipping requirement coverage is an error.
- Restore the upstream apply instruction verbatim and append the project requirements after it.
- Relabel the review-workflow benchmark as illustrative, drop the unsupported precision claim, and
  list the prompts, transcripts, and execution records that were not preserved.

## Impact

- Affected specs: new `openspec-verification-workflow` capability delta.
- Affected code: `scripts/openspec_quality_gate.py`, `scripts/openspec_tasks.py`,
  `scripts/openspec_validate_changed.py`, `scripts/change_acceptance.py` import path,
  `.github/workflows/ci.yml`, and `pyrightconfig.json`.
- Affected guidance: `openspec/schemas/evidence-driven/`, `openspec/README.md`,
  `guidance/openspec-workflow.md`, and `docs/benchmarks/openspec-review-workflow.json`.
- No change to product behaviour, API contracts, data, or the scientific model.
