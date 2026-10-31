# Adversarial review — strengthen-openspec-verification-workflow

> **Status: post-implementation (retrospective).** This review was written after the code
> existed, during final remediation of an already-implemented change set. It is not
> pre-implementation approval, it was not written before `tasks.md`, and the change record
> itself is retrospective. The reviewer is the agent that performed the remediation, so this
> is a self-review: finding AR-7 records that limitation rather than hiding it.

- Scope: the evidence-driven OpenSpec hardening delivered in two phases (preflight/contract,
  then enforcement: schema-version freeze, changed-only CI validation, task-marker counting,
  evidence-reference rules, skip policy, upstream instruction preservation, benchmark labels).
- Inputs: the earlier independent acceptance review (CONDITIONAL PASS, findings B1-B6), the
  remediation diff, the four changed scripts, the CI workflow, and the retained test suite.
- Method: re-attack each previously verified bypass, then read the new code paths for new
  bypasses and untested paths. Ground truth for the earlier defects comes from recorded probe
  output; ground truth for this review is the code and tests in this repository.

## Decision

PASS_WITH_WARNINGS — every previously reported bypass is closed and regression-tested; the
open findings are limitations of evidence and independence, not known exploitable gaps.

## Findings

| ID | Severity | Verification | Status | Finding |
|---|---|---|---|---|
| AR-1 | BLOCKING | VERIFIED | RESOLVED | New changes could declare `schema_version: 2` to inherit the lax pre-contract checks. Fixed by the frozen-name allowlist in `scripts/openspec_quality_gate.py:406` plus `GATE-RECORD-VERSION-LEGACY`; regression test `test_new_change_cannot_declare_legacy_version`. Evidence: the same lax record now exits 1, while a frozen legacy change still passes. |
| AR-2 | BLOCKING | VERIFIED | RESOLVED | CI could report success while validating zero changes after a depth-1 checkout. Fixed in `scripts/openspec_validate_changed.py`: explicit per-event base, exit 2 on unresolved base or base == HEAD; simulated in disposable repositories by `test_shallow_checkout_cannot_report_success` and `test_missing_base_fails_explicitly`. |
| AR-3 | BLOCKING | VERIFIED | RESOLVED | Markers such as `[~]` and `[-]` hid unfinished tasks. Fixed in `scripts/openspec_tasks.py`: every checkbox-like marker is counted, only `[x]`/`[X]` complete, non-standard markers warn; matrix covered by `scripts/tests/test_openspec_tasks.py`. |
| AR-4 | MAJOR | VERIFIED | RESOLVED | The gate template defaulted evidence to agent-authored QA prose and did not say a pointer is not proof. Template now uses an explicit placeholder, and guidance/templates state the pointer/proof distinction; no rule pretends to authenticate evidence. |
| AR-5 | MAJOR | VERIFIED | RESOLVED | `--skip-openspec` could be passed at acceptance and demote requirement coverage to warnings. Readiness now errors with `GATE-OPENSPEC-SKIPPED`; planning-stage skips still warn. Test: `test_readiness_rejects_skipped_requirement_coverage`. |
| AR-6 | MAJOR | VERIFIED | RESOLVED | The project schema replaced the upstream `apply` instruction instead of appending to it. Upstream text is restored verbatim and project requirements follow it; checked by a substring test against the installed spec-driven schema. |
| AR-7 | MAJOR | JUDGMENT | OPEN | No independent reviewer: the same agent implemented and reviewed this change, and the earlier acceptance review also shared repository context. Human acceptance must weigh that; the gate cannot. |
| AR-8 | MINOR | VERIFIED | OPEN | The v2 allowance is keyed on the change directory name, so re-creating a directory with one of the 16 frozen names would inherit it. Archive moves the directory, so this needs a deliberate name reuse; a content fingerprint would remove it but adds new record metadata. |
| AR-9 | MINOR | SUSPECTED | OPEN | On a force-push, `GITHUB_EVENT_BEFORE` can name an unreachable commit; fetch-depth 0 does not fetch it, so CI fails with "base does not resolve" instead of validating. Not reproduced in a real repository; it fails loudly rather than silently. |
| AR-10 | MINOR | UNVERIFIED | OPEN | Real GitHub Actions behavior is not executed here: the tests simulate events with disposable repositories. That `fetch-depth: 0` materializes `origin/<base>` and that the env values arrive as configured is reasoned from the workflow file, not observed in a run. |
| AR-11 | MINOR | VERIFIED | OPEN | The checkbox regex accepts at most three marker characters, so `- [wip]` reads as a plain bullet. Unfinished work is then absent from the total rather than counted as done, which matches the schema instruction that only checkbox lines are tracked. |
| AR-12 | MINOR | VERIFIED | RESOLVED | The benchmark claimed precision it never recorded. `docs/benchmarks/openspec-review-workflow.json` now declares `precision: null`, classification `illustrative`, and the missing artifacts; label test `scripts/tests/test_openspec_benchmark_labels.py`. |

## Untested paths carried forward

- A real pull request, push, and shallow-checkout run in GitHub Actions (AR-10).
- A force-push whose previous commit is unreachable (AR-9).
- Any owner-acceptance decision: no `owner-decision.json` exists for this change.

## What this review is not

It is not an independent review, not proof that the recorded commands ran, and not a
substitute for human acceptance. The gate records these states; it does not authenticate them.
