# Code review — strengthen-openspec-verification-workflow

> **Status: post-implementation (retrospective).** Written after the code was complete, by the
> agent that wrote it. It is not an independent review; see AR-7 in `adversarial-review.md`.

Scope: `scripts/openspec_quality_gate.py`, `scripts/openspec_tasks.py`,
`scripts/openspec_validate_changed.py`, `scripts/change_acceptance.py`,
`.github/workflows/ci.yml`, `Makefile`, and the tests that exercise them.

Method: read the new code paths end to end, then trace each previously demonstrated bypass
through the current code. No mutation testing, no independent second reader.

## Decision

PASS_WITH_WARNINGS.

## Findings

| ID | Severity | Verification | Status | Finding |
|---|---|---|---|---|
| CR-1 | MINOR | VERIFIED | RESOLVED | Task counting used to live in two places. `scripts/change_acceptance.py:206` now delegates to `scripts/openspec_tasks.py` (`from scripts.openspec_tasks import task_counts as count_tasks`, line 22), so the gate and the acceptance CLI cannot disagree in code. |
| CR-2 | MINOR | VERIFIED | OPEN | Deleting a change directory is invisible to changed-only validation: `scripts/openspec_validate_changed.py` uses `git diff --diff-filter=d`, so a deletion produces an empty name list and a zero-change pass. Out of scope by design (the validator validates touched changes, not deletions) and worth knowing when the diff is only a removal. |
| CR-3 | INFO | JUDGMENT | OPEN | The gate records references and exit codes but cannot authenticate them; `emit()` says so in its note. Every pass therefore depends on reviewer honesty, which is a design property, not a defect. |
| CR-4 | MINOR | VERIFIED | OPEN | Each run on a frozen legacy record now emits `GATE-RECORD-LEGACY`. It keeps the frozen state visible, at the cost of noise in a sweep of all active changes. |
| CR-5 | MINOR | VERIFIED | RESOLVED | `changed_names()` treats a base that resolves to HEAD as an error instead of an empty diff, so the shallow-checkout failure mode can no longer look like a clean change set. Covered by `test_shallow_checkout_cannot_report_success`. |

## Behavioral notes

- Changed behavior: readiness rejects `--skip-openspec`; planning still warns.
- Callers: `make openspec-gate`, `make openspec-preflight`, `make change-status`, and CI
  `scripts/openspec_validate_changed.py`. No other caller passes `--skip-openspec` at readiness.
- Invariants relied on: a gate record cannot lower strictness outside the 16 frozen names; a
  successful CI run always evaluated a resolved non-HEAD range.
- Untested paths: real Actions environment (AR-10), force-push with unreachable `before` (AR-9).
