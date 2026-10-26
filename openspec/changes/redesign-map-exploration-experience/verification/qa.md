# QA verification

## Automated

- `cd apps/web && npm test` — PASS, 74 tests.
- `cd apps/web && npm run typecheck` — PASS.
- `cd apps/web && npm run lint` — PASS.
- `cd apps/web && npx prettier --check src/components/dashboard.tsx src/components/dashboard.test.tsx src/app/globals.css e2e/dashboard.spec.ts playwright.config.ts` — PASS.
- `PLAYWRIGHT_PORT=3000 PLAYWRIGHT_EXTERNAL_SERVERS=1 PLAYWRIGHT_OUTPUT_DIR=/tmp/pw-reopen2 npm run e2e -- e2e/dashboard.spec.ts` — PASS, 10 tests across 1440×900 and 390×844; coordinate-click trajectory hit-layer regression included.
- `openspec validate redesign-map-exploration-experience --strict` — PASS.

## Browser evidence

Desktop and mobile mocked-API flows pass: 10/10 dashboard scenarios across 1440×900 and 390×844; coordinate-click regression passes on desktop. One Playwright trace-file cleanup failure was rerun successfully with trace disabled.

QA-owned isolated real runtime also passed at 1440×900 and 390×844: populated FastAPI web pair (`:3084` → `:8003`, 12 districts / 19,747 pipelines / 7 synthetic reports) and empty pair (`:3085` → `:8004`, zero imported features). Actual pointer flow passed: preview → advanced settings → Trajectory → path layer auto-enabled; aggregate summary replaced by trajectory summary; 0 console/page errors.

Additional QA: no horizontal overflow/clipping; axe-core 0 violations; contrast minimum 5.74; forced-colors and CDP 200%-layout checks pass. All five layer checkboxes measured 24×24 at 390px; final interactive-element check found no non-inline target under 24×24 after hit-area fixes. QA runtimes and databases were torn down.

## Task-target evidence

- 30-second orientation target: not formally timed; content is present in first-run orientation panel.
- Three-interaction target (area → configure → run): real browser flow completed, but no formal interaction-count study was run.

## Limitations

- The isolated real API populated browser workflow is verified above; localhost:3000 still has no FastAPI proxy, so repository `real-*` specs remain environment failures when run against that instance.
- OSM 503 wording was verified through frontend mock, not a live unavailable source.
- Pixel-level MapLibre network geometry alignment was not independently verified; browser-visible path layer, API geometry state, trajectory IDs, and layer legend were verified.
- OSM source-hash discrepancy from earlier evidence (`faae4ffd…` vs `5831ea28…`) remains a separate source-verification blocker; this change does not alter source artifacts.
- No WCAG certification claim. Keyboard/focus, reduced-motion CSS, axe-core, contrast, forced-colors, CDP 200%-layout, and touch-target checks passed; VoiceOver/screen-reader, true browser zoom, and physical touch hardware remain unexecuted.
- Municipal Analyst re-evaluation passed orientation, study area, simulation, actual Trajectory selection, aggregate separation, path-layer state, reports, and provenance. Screenshot capture timed out, so pixel-level curvature remains unverified.
