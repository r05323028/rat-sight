# Design

## Local CLI

`scripts/change_acceptance.py` uses only Python standard-library modules. It validates change names and paths, summarizes existing proposal/tasks/gate/Git state, invokes the existing quality gate for review, and emits JSON for status tooling.

## Decision storage

`verification/owner-decision.json` contains `schema_version`, `change`, `current`, and append-only `history`. Each decision records status, timestamp, source, reviewed commit, working-tree state, and a SHA-256 fingerprint of all change files except the decision file. Atomic replacement prevents partial writes. The local CLI documents that TTY safeguards do not authenticate the OS user.

## Archive boundary

The Makefile wrapper runs the existing gate, then checks the current decision through the CLI in a non-interactive status mode. It invokes native `openspec archive` only after current `ACCEPTED` status, matching fingerprint, and a passing gate. Uncommitted state is recorded explicitly; the fingerprint remains the reviewed implementation identity. Direct upstream `openspec archive` remains an acknowledged bypass.

## Policy boundary

Existing `verification/acceptance.md` and `approval` handling remain reserved for mandatory policy approvals and accepted-risk findings. They are not replaced by owner-decision records.
