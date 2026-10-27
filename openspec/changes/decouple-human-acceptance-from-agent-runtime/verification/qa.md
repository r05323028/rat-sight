# QA

Decision: PASS_WITH_WARNINGS.

## 2026-10-27 corrective addendum — implementation snapshot and task readiness

- The prior fingerprint covered the OpenSpec change directory only. `/Users/seanchang/rat-sight/scripts/change_acceptance.py` now hashes every committed Git tree entry by path, mode, and blob, excluding only the current change's `verification/owner-decision.json`. The reviewed commit remains recorded separately as audit identity.
- Source, API schema, frontend, test, migration, configuration, and OpenSpec evidence changes therefore invalidate an earlier acceptance. The decision file itself does not self-invalidate, including after a commit that changes only that file.
- Dirty detection uses full-repository NUL-delimited porcelain for staged, unstaged, and nonignored untracked files. The owner-decision record is the only exemption. A final acceptance refuses an unidentified implementation snapshot; it does not commit or clean the owner's work.
- Readiness now requires a nonempty completed required-task list, verification/code-review evidence, a passing Quality Gate, required policy approval, and a clean snapshot. Empty or missing `tasks.md` is not completion. Explicit non-goal/future-follow-up/out-of-scope/not-required sections are excluded from required counts.
- The archive wrapper rejects missing/stale/dirty snapshots, incomplete tasks, failed evidence/gate, missing policy approval, and `CHANGES_REQUESTED`/`DEFERRED` decisions.
- `/Users/seanchang/rat-sight/scripts/openspec_quality_gate.py` now also fails closed with `GATE-TASKS-MISSING`, `GATE-TASKS-EMPTY`, or `GATE-TASKS-INCOMPLETE`; recorded PASS artifacts can no longer report readiness while required tasks remain open.
- `uv run pytest scripts/tests/test_change_acceptance.py -q`: **13 passed in 3.92s**. Cases cover source/API/test/evidence invalidation, decision-only commit stability, missing tasks, staged/unstaged/untracked dirt, stale archive rejection, a valid current preflight, and preserved Request Changes/Defer history in isolated temporary repositories.
- `uv run pytest scripts/tests/test_openspec_quality_gate.py scripts/tests/test_change_acceptance.py -q`: **35 passed in 43.08s**.
- Final repository regression: `make test-py` **209 passed in 103.69s** (including both acceptance and quality-gate suites); `make test-js` **64 passed**; `make typecheck`, `make lint`, `make format-check`, and `make build` passed.
- Limit retained: terminal confirmation is not cryptographic authentication. No owner acceptance was written and this change was not archived.

- `uv run pytest scripts/tests/test_change_acceptance.py -q`: 5 passed.
- OpenSpec strict validation passed.
- Read-only review and status paths were exercised against the active change.
- Temporary-repository tests covered path traversal, fingerprint exclusion, append-only history, feedback persistence, and archive rejection without owner acceptance.
- Warning: full interactive TTY menu and native archive success were not automated; acceptance remains human-owned and this change is not self-accepted.
