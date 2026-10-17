# Independent stabilization code review

**Reviewer:** verification-reviewer
**Scope:** current stabilization diff: migrations 0005/0006, seed/reset and smoke harness, persisted classification validation, dashboard list/map selection/invalid-time handling, tests and live-E2E assertions.
**Decision:** PASS.

## Finding

### CR-STAB-001 — HIGH / RESOLVED: frontend production build failed TypeScript checking

**Resolution verified:** the provenance block now consistently dereferences narrowed `activeRodentReports`, eliminating the nullable `rodentReports` access.

## Positive observations

- Migration `0005` constrains persisted classification to `SIMULATED`; application reads now validate both `data_class` and classification and raise a data-contract error rather than relabeling rows.
- Migration `0006` recreates the immutability function/trigger for existing databases and does not weaken the guard. The smoke harness checks the trigger after each migration and resets only by destroying its project-scoped disposable volume, not by deleting immutable rows.
- Seed/reset behavior is explicit: populated mode imports the pinned fixture; empty mode only verifies a freshly recreated empty database and refuses a non-empty database.
- Dashboard retains all returned features in MapLibre while capping auxiliary buttons, derives selected details from current response data, and locally rejects reversed time ranges before querying.
- Existing test additions cover classification mismatch, list cap, map selection, invalid ranges, stale data, and trigger/reset behavior.

## Verification run

- `uv run --package ratsight-api pytest services/api/tests/test_rodent_reports_import.py services/api/tests/test_rodent_reports_api.py` — **55 passed**.
- `corepack pnpm --filter @ratsight/web test -- --run` — **46 passed**.
- Targeted backend Ruff — **passed**.
- `corepack pnpm --filter @ratsight/web build` — **passed**, including TypeScript checking.
- `corepack pnpm --filter @ratsight/web e2e` — **5 passed, 7 skipped**; controlled checkbox toggles use click/assertions and no race was observed.
- Focused live rodent/stormwater smoke was not rerun in this review; existing QA evidence remains separately recorded.
- No implementation files were edited during review.

## Verdict

**PASS:** CR-STAB-001 is resolved. Frontend tests and production build pass; no scientific classification regression was found. Original review did not detect the cleanup isolation defect documented as CR-STAB-002 below. Live smoke remains represented by the existing QA evidence and was not rerun in the original focused review. No implementation files were edited during the original review.

## Follow-up review (2026-10-17)

**CR-STAB-002 — MAJOR / RESOLVED: smoke cleanup killed unrelated listeners.** The EXIT trap ran `stop_services` even on preflight failure, and the old `lsof`/`kill -9` loop could terminate any process listening on fixed web/API ports 3008/8008. Removed generic listener lookup and killing; cleanup now terminates only process trees rooted at this script's tracked `WEB_PID`/`API_PID`. `bash -n` passed. A forced Docker-unavailable preflight probe with an unrelated listener on port 8008 exited 3 as expected and confirmed the listener remained reachable (evidence in `verification/qa.md`). This is an implementation-agent follow-up, not a new independent review.
