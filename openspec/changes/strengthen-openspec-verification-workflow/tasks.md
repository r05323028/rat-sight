# Tasks

## Retrospective record

- [x] 1. Record that this change was implemented before its OpenSpec record existed, with no pre-implementation preflight approval.
- [x] 2. Cite the acceptance review that judged the uncommitted work instead of inventing a prior adversarial review.

## Implementation

- [x] 3. Freeze `schema_version: 2` to the sixteen existing change records; reject it elsewhere with `GATE-RECORD-VERSION-LEGACY` and evaluate the record as v3; warn `GATE-RECORD-LEGACY` for frozen records.
- [x] 4. Resolve the CI diff base from the pull-request base, the push `before` commit, or the default branch; exit 2 on an unresolved, HEAD-resolving, or failed range; report a resolved zero-change range distinctly.
- [x] 5. Replace the duplicate task counters with `scripts/openspec_tasks.py`: count every marker, complete only `[x]`/`[X]`, warn `GATE-TASKS-MARKER` for other non-empty markers.
- [x] 6. Default the gate template's verification reference to a CI artifact placeholder and state in the template and guidance that a reference is a pointer, not proof.
- [x] 7. Make `--skip-openspec` an error at readiness and keep it a warning at planning.
- [x] 8. Restore the upstream apply instruction verbatim and append the project requirements after it.
- [x] 9. Relabel `docs/benchmarks/openspec-review-workflow.json` as illustrative, null the precision field, and list the artifacts that were not preserved.
- [x] 10. Fetch full history in the Python CI job and pass the event variables to the changed-only validator.

## Verification

- [x] 11. Add regression tests for the version freeze, the CI base resolution, and the marker matrix, and run the full `scripts/tests` suite (98 passed).
- [x] 12. Run `ruff`, `basedpyright`, `openspec schema validate evidence-driven`, and the gate on all active changes to confirm the frozen records keep their decisions.

## Status

Retrospective record. Implementation is complete and the verification tasks above passed.
`verification/gate.json` is intentionally absent: no adversarial or code review record exists for
this change, and this record does not invent one. The quality gate therefore reports
`GATE-RECORD-MISSING` until a real review is performed and its findings, decisions, and evidence
are recorded.
