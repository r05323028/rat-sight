# QA verification

Executed by `verification.qa` (independent of the author) on 2026-10-21. Every entry below was
actually run in this worktree; commands and exit codes are copied from the run, not inferred.

## Automated checks

- `cd apps/web && corepack pnpm exec vitest run src/components/dashboard.test.tsx src/components/map-view.test.tsx src/lib/api.test.ts` — exit 0, 3 files / 57 tests passed.
- `corepack pnpm --filter @ratsight/web typecheck` — exit 0 (`tsc --noEmit`).
- `make lint` — exit 0 (ESLint: no output/no problems; `uv run ruff check .`: "All checks passed!").
- `make build` — exit 0 (`next build`: compiled successfully, TypeScript finished, 3/3 static pages generated).
- `openspec validate stabilize-local-analyst-workflow --strict` — exit 0 ("Change 'stabilize-local-analyst-workflow' is valid").
- `make geospatial-smoke` — exit 0, 4 browser specs passed: `real-api.spec.ts`, `real-api-empty.spec.ts`, `real-stormwater.spec.ts`, `real-stormwater-empty.spec.ts`.
- `make rodent-report-smoke` — exit 0, 2 browser specs passed: `real-rodent-report.spec.ts` populated and empty.
- Municipal Analyst browser review at approved isolated `http://127.0.0.1:3010` — PASS: populated reports, Taipei date filtering, empty/reversed ranges, district/pipeline provenance, and seed-42 simulated preview verified.
## Isolated populated runtime evidence

`make geospatial-smoke` launches exactly the documented isolated shape: PostGIS on
`127.0.0.1:55439` from a project-scoped disposable volume, API on `127.0.0.1:8010`, web on
`127.0.0.1:3010`, `CORS_ORIGINS=http://127.0.0.1:3010,http://localhost:3010`,
`NEXT_PUBLIC_API_URL=http://127.0.0.1:8010`, with `next dev` (so `allowedDevOrigins` is in effect).
It checks `/health`, then drives real browser sessions at `http://127.0.0.1:3010`.

Hydration is evidenced by those specs rather than by a separate micro-probe: `real-api.spec.ts`
requires client-side rendering of district data fetched at runtime through the API, which cannot
pass if the client bundle does not hydrate. No dedicated `__reactProps` probe was run.

`make rodent-report-smoke` uses ports 55448/8008/3008 with its own project-scoped disposable volume
and proves the end-to-end Taipei conversion: filling `2026-10-10T08:00` (Asia/Taipei) produces a
request with `reported_from=2026-10-10T00%3A00%3A00Z`, and the response echoes
`reported_from: "2026-10-10T00:00:00Z"`.

## Interference disclosure

Port `55448` was held by a leftover disposable stack `ratsight-rodent-report-smoke-2798` (only its
PostGIS container running, no API/web services, ~12 min old) from an earlier run of the same
harness, which blocked `make rodent-report-smoke`. It was removed with the harness's own teardown,
`docker compose -p ratsight-rodent-report-smoke-2798 down -v --remove-orphans`. The shared dev
services (`infra-postgres-1` on 54329, `infra_ratsight-postgres-data`) and the unrelated process on
port 3000 were not touched. After both runs no ratsight container or harness port remained.

## Retained analyst runtime (operational, not a verification claim)

`make geospatial-smoke` cannot be retained: it traps `down -v` on exit and finishes in the
`SMOKE_EMPTY` state. To enable the municipal-analyst black-box pass, QA kept an equivalent stack up
from `/tmp/ratsight-qa-runtime/launch.sh` (outside the repository; no repo files changed):

- web `http://127.0.0.1:3010`, API `http://127.0.0.1:8010` (`/health` 200)
- compose project `ratsight-qa-analyst-runtime`, project-scoped volume, ports 3010/8010/55439
- populated synthetic fixtures: 1 district (`smoke-fixture`), 1 stormwater pipeline, 5 rodent
  reports (`00000000-0000-4000-8000-000000000002`); single-seed row counts re-verified after a
  repeat seeding run
- teardown owner: QA, via `/tmp/ratsight-qa-runtime/teardown.sh`

- teardown owner: QA, via `/tmp/ratsight-qa-runtime/teardown.sh`

The runtime was **torn down 2026-10-21T15:51:53Z** and cleanup verified: no
`ratsight-qa-analyst-runtime` container, no project volume, and ports 3010/8010/55439 free. The
shared `infra_ratsight-postgres-data` volume and its `infra-postgres-1` service were left alone.

Two teardown defects were found and fixed in the script, both worth remembering:

- killing whatever listens on 55439 also kills Docker Desktop's own backend, which takes the daemon
  down mid-teardown; only `docker compose down -v` should remove that container
- the generated override has no image/build context, so `down` needs both files:
  `docker compose -p <project> -f infra/docker-compose.yml -f override.yml down -v`

## Layer control evidence (R3)

The municipal analyst reported four live checkboxes (Administrative districts, Stormwater pipelines,
Rodent reports, Simulated movement paths). That is the expected behaviour, and a headless probe on
the retained runtime confirmed both states:

- before running a preview: exactly 3 checkboxes (`Administrative districts`, `Stormwater pipelines`,
  `Rodent reports`) - the three built-in available layers; every catalog row renders
  `<span class="layer-status">Not loaded</span>`
- after `Run synthetic preview` (seed 42): 4 checkboxes, `Simulated movement paths` gaining one, and
  the analysis panel reporting 16 synthetic edges / 312 synthetic node visits

An earlier note in this session that "only simulated-paths carries a live checkbox" was wrong; correct
is: built-in available layers plus simulated paths once the preview has produced a graph.

## Observations (not defects of this change)

- The first `make lint` invocation in this session reported 345 errors with paths under the
  generated `.next-ratsight-*` smoke build directories. `apps/web/eslint.config.mjs` now ignores
  `.next-*/**`, and the re-run passed. Not a defect of the change; it was a lint-scope gap in the
  smoke harness output being linted, fixed in the same worktree.
- `adversarial-review.md` rates AR-LAW-004 and AR-LAW-005 `MEDIUM`, but `scripts/openspec_quality_gate.py`
  only accepts `BLOCKING|MAJOR|MINOR|INFO`, so `gate.json` records both as `MINOR`.

## Not verified

- No authoritative-data workflow, real Taipei counts, or real-world rodent observations were tested.
- No dedicated fresh-browser hydration micro-probe; hydration is inferred from the passing
  client-rendered browser specs above.
- Municipal Analyst review covered synthetic fixtures only and is not municipal decision readiness.
