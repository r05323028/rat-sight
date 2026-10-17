# Independent QA — stabilize-rodent-report-integration

**Verdict: CLEAR** — stabilization behavior and the requested verification suites are green after hardening the controlled-checkbox test interaction.

- Qitem: `qitem-20261017164827-62392bd60630ffa8`
- Evaluator: `verification.qa@rat-team`
- Candidate: uncommitted stabilization diff on `main` at `a5f3c38`
- Date: 2026-10-17
- Scope: independent, read-only. No implementation file edited.

## Commands and results

| # | Command | Result |
|---|---------|--------|
| V1 | `openspec validate stabilize-rodent-report-integration` | **valid** |
| V2 | `uv run pytest -q` | **174 passed** |
| V3 | `corepack pnpm --filter @ratsight/web test` | **3 files / 46 tests passed** |
| V4 | `corepack pnpm --filter @ratsight/web typecheck` | **pass** |
| V5 | `corepack pnpm --filter @ratsight/web lint` | **pass** |
| V6 | `corepack pnpm --filter @ratsight/web format:check` | **pass** |
| V7 | `corepack pnpm --filter @ratsight/web build` | **pass** (exit 0; CR-STAB-001 fixed) |
| V8 | `corepack pnpm --filter @ratsight/web e2e` (full, 4 workers) | **5 passed, 7 skipped** after replacing flaky controlled-checkbox `check()` calls with click + assertion |
| V9 | `... playwright test e2e/dashboard.spec.ts` (whole file) | **5 passed** |
| V10 | `make rodent-report-smoke` | **pass** both scenarios — populated 1 passed/1 skipped; storage-empty 1 passed/1 skipped (2 consecutive clean runs) |
| V11 | `make geospatial-smoke` | **pass on retry** — 4/4 real-API specs; one first attempt failed transiently on the stormwater toggle |
| V12 | `uv run basedpyright` | **0 errors, 0 warnings, 0 notes** |
| V13 | `uv run ruff check`/`format --check` on feature files; `bash -n` both smoke scripts | **clean / OK** |
| V14 | `uv run ruff check .` (repo-wide) | **13 E501**, all in untracked `.agents/skills/sem/**` (outside this change) |

## Stabilization items verified

- **CR-STAB-001 (build) FIXED:** the provenance block in
  `apps/web/src/components/dashboard.tsx` now dereferences the narrowed
  `activeRodentReports.provenance`; `next build` TypeScript checking passes (V7). The recorded
  `verification/code-review.md` decision `BLOCKED` is stale relative to the working tree.
- **Migrations 0005/0006:** `0005_rodent_reports_simulated` replaces the classification CHECK
  with `classification = 'SIMULATED'` (downgrade restores the epistemic vocabulary);
  `0006_rodent_reports_immutability` idempotently `CREATE OR REPLACE`s the immutability
  function and recreates the `rodent_reports_immutable` trigger for databases that applied
  `0004` before the trigger existed. Neither weakens the guard.
- **Immutable smoke reset:** `scripts/seed_rodent_report_smoke.py` no longer deletes rows;
  empty mode verifies a freshly empty disposable DB and exits `3` if rows exist. The smoke
  script recreates its project-scoped disposable volume for the populated→empty transition
  and asserts the trigger is present after migration. Both scenarios passed (V10).
- **Classification consistency:** application reads validate persisted `data_class` and
  classification and raise a data-contract error rather than relabeling; covered by the
  expanded importer/API tests (V2/V3).
- **Bounded inspection + temporal validation:** dashboard caps auxiliary report buttons at 100,
  retains all MapLibre features, derives selection from current features, and rejects
  reversed time ranges locally. Covered by unit tests and the live smoke.
- **Isolation/cleanup:** after every smoke run there were no listeners on the smoke ports, no
  smoke containers/volumes/networks, and the shared `infra-postgres-1` container and
  `infra_ratsight-postgres-data` volume were untouched. No real report data was used.

## Finding

### QA-STAB-001 — MEDIUM — RESOLVED: full parallel web e2e controlled-checkbox race

Running the whole default e2e suite (12 tests, 4 workers) failed twice on
`e2e/dashboard.spec.ts:337` at `await toggle.check()` for the controlled `Rodent reports`
checkbox:

```text
Error: locator.check: Clicking the checkbox did not change its state
  - locator resolved to <input type="checkbox" aria-label="Rodent reports"/>
  - performing click action / click action done
```

The same test passes in isolation, and the whole `dashboard.spec.ts` file passes **5/5** when
run alone (V9). The same `check()` race also appeared once on the stormwater toggle during the
first `make geospatial-smoke` attempt (V11), which then passed on retry. Evidence of the
environment condition: `vm_stat` showed ~69 MB free; a `--workers=1` full e2e run was killed
with exit 137 (SIGKILL).

**Root cause:** `locator.check()` on a React-controlled checkbox clicks and then verifies the
DOM `checked` state; under load the re-render/state update can lag the click, so React resets
`checked` to false. This is a pre-existing test-harness pattern (the test file is unchanged by
the stabilization), amplified by cross-file parallelism on a memory-constrained host. It is
not a product defect: the toggle works in isolation and the smokes exercise the same control
successfully.

**Resolution:** `apps/web/e2e/dashboard.spec.ts` now uses `click()` followed by the existing
`toBeChecked()` assertions for controlled administrative, stormwater, and rodent toggles.
The full default suite then passed 5/5 active tests and 7 intentional skips.

## Limitations

- The initial full default e2e failure was reproduced and resolved as a test-harness race; the final full suite passed.
- `make geospatial-smoke` passed only on retry (first attempt hit the same toggle race).
- The smoke suites are heavier than before (multiple containers/dev servers); on this host the
  first attempt after other heavy runs is unreliable.
- Repo-wide `ruff`/`format` remain red only because of the untracked third-party
  `.agents/skills/sem/**` + `skills-lock.json`; feature files are clean.

## QA position

The stabilization's target behaviors are verified and the blocking build finding is resolved.
The stabilization's final backend/web suites, rodent smoke, geospatial smoke, and default
e2e are green. QA-STAB-001 is resolved. As follow-up hardening, all remaining real/official
E2E controlled-toggle interactions now use click plus checked-state assertions. A subsequent
full default E2E run passed 5/5 active tests with 7 intentional skips. I return **CLEAR**.

### QA focused re-verification (2026-10-17, verification.qa)

Independently reproduced the fix and re-ran the formerly failing target:

- `corepack pnpm --filter @ratsight/web e2e` run 1 -> **exit 0, 5 passed / 7 skipped**
- `corepack pnpm --filter @ratsight/web e2e` run 2 -> **exit 0, 5 passed / 7 skipped**
- `playwright test e2e/dashboard.spec.ts` (whole file) -> **5 passed**

Focused rerun limitation: QA could not rerun `real-api.spec.ts`, `real-stormwater.spec.ts`,
`real-rodent-report.spec.ts`, or `official-district.spec.ts` after the Docker daemon went down
mid-session (`UNVERIFIED/NOT RUN: rodent report smoke unavailable (Docker daemon is unavailable)`,
exit 3). Earlier recorded runs passed when Docker was available (V10/V11). A source check found no
remaining `.check()`/`.uncheck()` calls in `apps/web/e2e/`; the controlled-toggle follow-up is
resolved in source. This does not replace rerunning those Docker-backed tests.

### Cleanup isolation re-verification (2026-10-17)

- `bash -n scripts/rodent_report_smoke.sh` -> **pass**.
- Targeted preflight probe: a temporary unrelated HTTP listener occupied port 8008; a PATH-injected Docker stub forced the Docker-unavailable preflight. The smoke script exited 3 as expected, and the listener remained alive and served HTTP after EXIT cleanup. Temporary process and files were removed; no smoke stack started.
- This verifies preflight cleanup isolation only; it does not rerun the full populated/empty smoke scenarios.
