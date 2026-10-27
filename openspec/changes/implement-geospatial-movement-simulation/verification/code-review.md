# Code review

## Decision

PASS WITH WARNINGS. Backend and frontend changes preserve explicit graph-node origins, bounded returned geometry, deterministic step identity, and synthetic-only labeling. Automated and isolated real-runtime checks are recorded in `qa.md`.

## Findings and disposition

- **CR-008 — MAJOR, IMPLEMENTED / AUTHENTICATION PENDING:** User message m00160 requires explicit `study_area`; requests now return validation error when omitted, and callers/tests pass it explicitly. The chat message has no project-approved human identity/provenance visible to this agent, so formal finding closure remains pending authentication. This choice does not constitute acceptance or archive approval.

No new security, data-loss, or silent-origin-snapping issue was found in this change.

## Task 12 role evidence

- Public Health: **CONDITIONAL**, limited to bounded synthetic surface-network simulation; no report-origin or biological interpretation approval. Evidence: `verification/qa.md`, `docs/evidence/network-aligned-movement-2026-10-23.md`.
- Modeler: **CONDITIONAL**, diagnostics and step semantics acceptable; fresh runtime evidence and final OpenSpec/QA closure remain pending.
- Reviewer: **CONDITIONAL**, CR-008 and role-specific sign-offs remain open. F1 stormwater accessible-name mismatch is fixed and browser-verified.
- Municipal Analyst: **PASS**, read-only black-box re-evaluation on QA-owned `127.0.0.1:3086` → API `8005`. Origin semantics, playback, reachability/unsampled disclosure, truncation, and non-biological safeguards passed; no UX finding.

## Follow-up self-review (2026-10-26; updated 2026-10-27)

- Reviewed focused test diff and walker implementation: sink test exercises early termination after final edge; isolated-origin test confirms empty trajectory, normalized origin visit, and empty edge results. No model behavior changed.
- Current pinned expanded artifact hashes to `9db94dd723445fb45e73a77dca4ee4a74783af26e04794fc3fc9d5f63aa0f868`, matching loader expectation and current source records. Old songshan `faae4ffd...` and prior QA prefix `5831ea28...` are historical/unverified for their exact earlier bytes and are not current-source evidence.
- F1 stormwater accessible-name mismatch is fixed: the accessible name begins with the visible pipe label and appends the stable segment ID; focused dashboard and real-browser desktop/mobile checks pass.
- Explicit-field behavior is covered by regression tests, but CR-008 closure remains pending authenticated human provenance for m00160. This self-review is not Municipal Analyst, Public Health, Modeler, or Reviewer sign-off. Task 12 remains open pending the remaining role evidence and Municipal Analyst black-box reevaluation.
