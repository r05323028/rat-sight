# Verification: QA

Change: `localize-web-traditional-chinese` (zh-Hant hard switch for `apps/web`).
All commands below ran on 2026-10-23 in `/Users/seanchang/rat-sight`.

## Automated checks

| Check | Command | Result |
| --- | --- | --- |
| Unit tests | `cd apps/web && npm test -- src/components/dashboard.test.tsx src/components/map-view.test.tsx src/lib/api.test.ts` | PASS — 3 files / 58 tests |
| Typecheck | `cd apps/web && npm run typecheck` | PASS |
| Lint | `cd apps/web && npm run lint` | PASS |
| Production build | `cd apps/web && npm run build` | PASS — Next.js 16.4.2 |
| Dashboard e2e | `cd apps/web && corepack pnpm exec playwright test e2e/dashboard.spec.ts --reporter=line` | PASS — 5/5 (33.4 s) |
| Change validation | `openspec validate localize-web-traditional-chinese --strict` | PASS |

## Browser pass (production build, live API)

`next start --hostname 127.0.0.1 --port 3002` with `NEXT_PUBLIC_API_URL` defaulting to
`http://127.0.0.1:8000`; headless Chromium (Playwright) at viewport 1500x1000; probe
`/tmp/l10n-probe-final.mjs`.

Observed:

- `html lang="zh-Hant"`; title `見光鼠 RatSight · 都市鼠類移動分析`.
- Classification badges render `UNVERIFIED · 未驗證` (2) and `SIMULATED · 模擬` (3).
- Layer rows read `行政區…`, `雨水下水道管線…`, `鼠類回報 RODENT_REPORT · SIMULATED（模擬）`,
  `模擬移動路徑 SIMULATED · 合成測試資料；請執行預覽以產生` even though `/api/v1/layers`
  still returns English `label`/`message` values.
- Clicking `執行合成預覽` issued `POST /api/v1/simulations/preview` and showed
  `可重現執行完成 · 種子 42`; catalog row became available.
- No console errors; no `Mystery dataset`-style API prose leaked.
- Screenshot: `/tmp/ratsight-l10n-zh-final.png`.

## Earlier browser pass (dev server)

A prior pass against `next dev` on port 3002 produced the same zh-Hant results
(`/tmp/ratsight-l10n-zh.png`, probe `/tmp/l10n-probe.mjs`), including a successful synthetic
preview. That pass predates the unknown-layer fallback and detail-value gloss edits; the
production-build pass above is the post-fix evidence.

## Limits and unverified areas

- Only synthetic fixture data was exercised. No real observation dataset, importer, or
  authoritative-data workflow was tested (none is approved).
- API payloads remain English by design; UI copy is locale-owned. Remaining English body text is
  verbatim machine/provenance data (source names, dataset ids such as `ratsight-synthetic-graph-v1`,
  timestamps, seed values, license/attribution strings) required by the spec.
- A `__reactProps` hydration probe returned false even when the page was demonstrably
  interactive; hydration evidence therefore relies on successful interaction and network calls.
- Both servers used for verification were stopped after the pass.
