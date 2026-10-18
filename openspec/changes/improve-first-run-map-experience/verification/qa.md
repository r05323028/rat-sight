### Verification record

- `corepack pnpm --filter @ratsight/web exec vitest run src/components/dashboard.test.tsx` — PASS, 1 file / 24 tests.
- `corepack pnpm --filter @ratsight/web test` — PASS, 3 files / 52 tests.
- `corepack pnpm --filter @ratsight/web lint` — PASS.
- `corepack pnpm --filter @ratsight/web typecheck` — PASS.
- `corepack pnpm --filter @ratsight/web build` — PASS.
- `corepack pnpm --filter @ratsight/web format:check` — PASS.
- `uv run ruff check .` — PASS.
- `uv run ruff format --check .` — PASS.
- `git diff --check` — PASS.
- `openspec validate improve-first-run-map-experience` — PASS.

### Runtime boundary

The required initial municipal analyst evaluation was completed against `http://localhost:3000` and BLOCKED: that port served North `/login`, while RatSight API `127.0.0.1:8000` was unavailable. No browser PASS is claimed. Existing disposable smoke scripts remain the safe populated checks; they tear down their project-scoped stacks and were not rerun here because runtime ownership was unresolved.

### Post-implementation municipal analyst review

Scenario A completed successfully in a real browser at `http://localhost:3000`, read-only and without source/API/DB inspection or data mutation. Evidence: `/tmp/ratsight-scenarioA-map-report.png` and `/tmp/ratsight-scenarioA-simulation.png`.

Observed PASS: map pan/zoom, synthetic report selection (RR-0001), deterministic synthetic preview, and visible SIMULATED/provenance/uncertainty boundaries. The analyst confirmed no real administrative analysis is available. Follow-up frontend fixes now link the source-readiness register and documented operator-only import guides, remove the false empty-catalog error, and keep generated paths in a SIMULATED fixture group. The source-readiness-copy finding is addressed. Remaining: no approved source owner, license, or importer exists for real rodent observations, so authoritative-data acquisition remains blocked (MAJOR); Taipei-labelled schematic geometry retains minor interpretation ambiguity (MINOR). Scenario B and the real decision workflow remain untested by design. The analyst did not re-evaluate the frontend after these copy/grouping fixes; no authoritative data was ingested.

### Post-fix runtime acceptance (isolated instance, 2026-10-18)

The long-running RatSight dev instance at `http://127.0.0.1:3000` serves the post-fix markup but its client bundle does not hydrate for a fresh browser session (repeated `WebSocket connection to 'ws://127.0.0.1:3000/_next/hmr?id=…' failed: Error during WebSocket handshake: net::ERR_INVALID_HTTP_RESPONSE`; no React props on any node and zero `/api` requests after load and after clicking `Run synthetic preview`). It was not restarted or modified.

An isolated instance served the same sources instead: a byte-identical copy of `apps/web` (`rsync -a --exclude node_modules --exclude .next --exclude test-results`, untracked temporary directory `/Users/seanchang/rat-sight/.verify-first-run`) run with `NEXT_PUBLIC_API_URL=http://127.0.0.1:8000` on `http://127.0.0.1:3002` — an origin allowed by the API CORS default (`http://localhost:3000,http://127.0.0.1:3000,http://127.0.0.1:3002`). Read-only: no database, API, or repository file was modified. Headless Chromium (Playwright 1.64.1, probe `/tmp/ratsight-accept-3002.mjs`) verified:

- hydration confirmed (`__reactProps` present on the dashboard controls, so interactions are real);
- stale empty-catalog copy absent; synthetic group reads `Synthetic simulation | Simulated movement paths | SIMULATED · Synthetic fixture; run preview to generate`;
- unavailable group reads `Not loaded in this build` with the source-readiness link `https://github.com/r05323028/rat-sight/blob/main/docs/infrastructure/data-sources.md`;
- `Run synthetic preview` issued `POST /api/v1/simulations/preview`, produced `Reproducible run complete · seed 42`, switched the catalog row to `SIMULATED · Synthetic fixture`, and left the analysis panel showing SIMULATED provenance (`ratsight-synthetic-graph-v1`, synthetic node visits and edges) with `Simulated paths are not observed animal migration routes.`;
- with `GET /api/v1/layers` aborted, the group switches to `Layer catalog unavailable` with retry guidance and no build/storage wording.

Evidence: `/tmp/ratsight-3002-layers.png`, `/tmp/ratsight-3002-preview.png`, `/tmp/ratsight-3002-catalog-outage.png`. Zero page errors were captured during the acceptance run.

Boundary: this verifies the post-fix UI contract against synthetic fixture data only. No approved source owner, license, or importer exists for real rodent observations, so Scenario B (authoritative data) and the real decision workflow remain untested. The isolated instance and its temporary directory are removed after the municipal analyst re-evaluation. The `:3000` instance remains non-interactive and no PASS is claimed for it.

An independent verification reviewer reran the web suite (3 files, 52 tests) with no actionable source defects. The stale test-count wording reported in that review is not present in the current artifacts: `verification/code-review.md` and `verification/gate.json` both record 52 tests, and dashboard-only runs are distinguished as 1 file / 24 tests.

### Post-fix municipal analyst re-evaluation (2026-10-18)

A read-only municipal analyst re-evaluation ran against the isolated instance at `http://127.0.0.1:3002` (synthetic fixture data only) through a real browser, closing the earlier "the analyst did not re-evaluate after the fixes" gap. Verdict: PASS, no remaining misleading wording found in the scoped pass. Observed copy: empty state "No real observation data loaded" with the source-readiness instruction naming and linking `docs/infrastructure/data-sources.md` and no invented sources; the catalog separates `RODENT_REPORT · SIMULATED` and the "Synthetic simulation" group from "Not loaded in this build"; the preview produced `Reproducible run complete · seed 42` with provenance `ratsight-synthetic-graph-v1`, 16 synthetic edges, and 312 synthetic node visits, alongside `Synthetic preview — simulated fixture only; no real observations or administrative findings. This output cannot support real administrative decisions.` and `Simulated paths are not observed animal migration routes.`; report filter copy reads `5 reports match the current viewport and reported-date filter (UTC, inclusive)` with `Synthetic report-shaped fixtures. Not verified observations, prevalence, population, movement, or risk evidence.`

The re-evaluation explicitly did not verify authoritative-data Scenario B, real sources or importers, or real Taipei counts. Evidence: `/tmp/ratsight-postfix-synthetic.png`. The verdict is recorded in queue transition 389 of `qitem-20261018142728-a4db2e061174ca73` (closed `no-follow-on`), and it states that the post-fix copy resolves the earlier source-readiness-copy finding. No implementation or data changes were made by the analyst.

For a future authoritative-data pass, use a project-scoped PostGIS volume and non-conflicting ports (for example API 8010/web 3010), run existing seed scripts only for synthetic fixtures, and tear down with `docker compose ... down -v`. Do not use shared default volume or ingest live data.
