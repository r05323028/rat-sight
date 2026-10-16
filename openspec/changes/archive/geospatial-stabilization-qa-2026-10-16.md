# QA — geospatial stabilization (2026-10-16)

**Verdict: CLEAR** for the current stabilization diff.

- Qitem: `qitem-20261016161104-d3ca1f8109ac4139`
- Evaluator: `verification.qa@rat-team` (not an author of the change)
- Scope: uncommitted stabilization diff on `main` at `fdf1ee4`. Read-only; no implementation edited.

## What the diff changes

- `apps/web/src/components/map-view.tsx`: highlight effect now also depends on `showBoundaries`
  so a selected district's highlight is restored after the boundary toggle is turned back on.
- `apps/web/e2e/real-api.spec.ts`: asserts the boundary toggle enables, selection sets
  `aria-pressed`, and selection survives toggle off → on against the real API.
- `apps/web/src/components/map-view.test.tsx`: added regression coverage for the highlight
  filter re-applied on a `showBoundaries` change.
- `docs/architecture/overview.md`, `README.md`: describe the available administrative layer and
  the isolated `make geospatial-smoke` harness, and keep non-observed limitations explicit.
- Archived `verification/gate.json` (both geospatial changes): `reference` paths corrected to the
  relocated `openspec/changes/archive/<date>-<change>/verification/...` files.
- `openspec/changes/archive/ARCHIVE-REFERENCE-NOTE.md`: documents the path-relocation correction.
- `guidance/lead.md`, `guidance/openspec-workflow.md`, `guidance/qa.md`: gate PASS is not
  acceptance/archival; QA records executed suites in `verification/gate.json`.

## Commands and results

| # | Command | Result |
|---|---------|--------|
| V1 | `corepack pnpm --filter @ratsight/web test` | **3 files / 13 tests passed** |
| V2 | `corepack pnpm --filter @ratsight/web typecheck` | **pass** |
| V3 | `corepack pnpm --filter @ratsight/web lint` | **pass** |
| V4 | `corepack pnpm --filter @ratsight/web format:check` | **pass** (Prettier clean) |
| V5 | `uv run pytest -q` | **81 passed** |
| V6 | `env POSTGRES_DB=wrong POSTGRES_USER=wrong POSTGRES_PASSWORD=wrong POSTGRES_PORT=54320 make geospatial-smoke` | **available spec 1 passed; empty spec 1 passed** |
| V7 | archived gate reference check (all `verification[].reference` + `engineering[].implementation/tests` in both archived `gate.json`) | **50/50 paths resolve**; no stale non-archive verification refs remain |

### Smoke detail (V6)

Reproduced the archived gate's V-SMOKE claim with deliberately conflicting inherited DB
settings. The script sanitizes `POSTGRES_DB/USER/PASSWORD/PORT`, uses a per-run isolated
project/volume, migrated `0001 → 0002`, and passed both real-API specs. Post-run state:
**no listeners on 3002 / 8000 / 55439**, **no smoke containers or volumes left**, and the
pre-existing dev `infra-postgres-1` untouched.

### Selection / toggle behavior

Confirmed by V1 (unit regression on the highlight filter after a `showBoundaries` change)
and V6 (the real-API spec checks the toggle, `aria-pressed` selection, toggle off, toggle
on, and that selection/provenance remain visible). The empty real-API spec confirms the
disabled toggle and "No boundaries imported" with no fabricated geometry.

## Standing finding (INFO, outside this stabilization's boundary)

`uv run ruff check .` still reports **13 E501 errors** and `uv run ruff format --check .`
reports **4 files** — all under the untracked `.agents/skills/sem/**` third-party skill
(`skills-lock.json`). Web-scoped lint/format and all Python tests pass. This is the same
unrelated repo-hygiene item previously reported; it needs an owner decision
(gitignore `.agents/`+`skills-lock.json`, or exclude `.agents` in `[tool.ruff]`). Not a
blocker for this stabilization.

## Limitations

- The archived gate `reference` correction was checked for path resolution, not by
  re-running the historical verification commands for every recorded V-ID.
- The official government archive was not re-downloaded in this pass.
