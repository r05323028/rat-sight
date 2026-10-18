# Tasks

## Specification

- [x] 1. Record black-box evidence and initial municipal analyst blocker.
- [x] 2. Define first-run state, layer clarity, simulation wording, and UTC filtering contracts.
- [x] 3. Complete adversarial review and carry unresolved runtime limitation into verification.

## Implementation

- [x] 4. Update dashboard layer catalog and empty/viewport/error guidance.
- [x] 5. Update simulation copy and report date/filter status without changing behavior or API.
- [x] 6. Document smallest safe populated local setup using existing seeders/smoke scripts; do not mutate shared state.
- [x] 7. Resolve sem Ruff scope and review AGENTS guidance with minimal separate maintenance change.

## Verification

- [x] 8. Run focused frontend tests, typecheck, lint, build, and formatting checks. Live smoke scripts remain unrun because the shared runtime is occupied by North.
- [x] 9. Independent code review and QA complete (verification reviewer PASS; web suite 3 files / 52 tests). Post-fix municipal analyst re-evaluation PASS 2026-10-18 against the isolated instance at `http://127.0.0.1:3002` (live API `http://127.0.0.1:8000`, synthetic fixture data only); authoritative-data Scenario B, real sources/importers, and real Taipei counts remain untested and out of scope.
- [x] 10. Complete gate records and run `make openspec-gate CHANGE=improve-first-run-map-experience`; stop at Ready for Human Review.
