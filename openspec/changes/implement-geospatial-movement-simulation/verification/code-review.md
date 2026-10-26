# Code review

## Decision

PASS WITH WARNINGS. Backend and frontend changes preserve explicit graph-node origins, bounded returned geometry, deterministic step identity, and synthetic-only labeling. Automated and isolated real-runtime checks are recorded in `qa.md`.

## Findings and disposition

- **CR-008 — MAJOR, resolved, then superseded 2026-10-26:** Owner selected restoring the legacy `taipei_synthetic_demo` default. A later owner decision (2026-10-26) reversed this to OSM-first defaults so simulated paths follow surveyed geometry; the schematic graph stays explicitly selectable, renders dashed with a 示意拓撲 note, and is never substituted for a missing extract. The resolution text below records the earlier decision. API schema and Dashboard now default to synthetic; OSM remains explicitly selectable and source-unavailability behavior is preserved for explicit OSM selection. API/UI regressions and full backend (162) and web (79) suites pass.

No new security, data-loss, or silent-origin-snapping issue was found in this change.

## Follow-up self-review (2026-10-26)

- Reviewed focused test diff and walker implementation: sink test exercises early termination after final edge; isolated-origin test confirms empty trajectory, normalized origin visit, and empty edge results. No model behavior changed.
- Current local artifact hashes to `faae4ffd1bd42e57871bdedbfdcc6e82b3324a458db95034d4ec40f0a019e67e`, matching loader expectation and current source records. Prior QA prefix `5831ea28d78c…` remains UNVERIFIED for its exact earlier bytes and is not used as current-source evidence.
- CR-008 resolved by owner decision and tested; this self-review is not Municipal Analyst, Public Health, Modeler, or Reviewer sign-off. Task 12 remains open pending role reviews and Municipal Analyst black-box reevaluation.
