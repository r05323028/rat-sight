# Tasks

- [x] Implement `scripts/change_acceptance.py` review/status/interactive decision workflow, safe paths, fingerprints, atomic history, and TTY safeguards.
- [x] Add Makefile `change-review`, `change-status`, and `change-accept` targets.
- [x] Require current owner acceptance in `openspec-archive` without changing native OpenSpec.
- [x] Add focused CLI and archive-wrapper tests using temporary repositories and synthetic decisions; do not modify historical decisions.
- [x] Update OpenSpec, Lead, and human-escalation guidance for policy approval vs readiness vs owner acceptance and durable requested changes.
- [x] Run validation, targeted tests, quality gate, and disposable acceptance/revision/defer/stale demonstrations.
- [x] Complete independent code review and QA; record evidence and stop at Ready for Human Review. Do not self-accept or archive.
- [x] Bind acceptance to the complete committed repository snapshot (path/mode/blob), exclude only the owner-decision record, detect staged/unstaged/nonignored-untracked changes, refuse final acceptance on a dirty implementation tree, derive readiness from nonempty completed tasks plus gate/evidence/policy approval, and enforce required tasks in the Quality Gate. (13 acceptance cases and 35 acceptance+gate tests pass; no owner decision written.)
