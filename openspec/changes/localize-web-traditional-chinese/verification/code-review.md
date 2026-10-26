# Code review

Change: `localize-web-traditional-chinese`. Reviewer: `verification-reviewer@rat-team`
(independent seat, read-only), queue item `qitem-20261023073951-016e8f8524a3ebc6`.

## Scope

Working diff for `apps/web/src/components/dashboard.tsx`,
`apps/web/src/components/map-view.tsx`, `apps/web/src/app/layout.tsx`,
`apps/web/src/components/dashboard.test.tsx`, `apps/web/src/components/map-view.test.tsx`,
`apps/web/e2e/*.spec.ts`, and the change artifacts. The peer dependency upgrade in
`apps/web/package.json` / `pnpm-lock.yaml` was out of scope.

## Decision

`DECISION: CHANGES-REQUESTED` → finding resolved → `PASS`.

- **L10N-CR-001 — MEDIUM — RESOLVED.** MapLibre navigation controls exposed English accessible
  names (`Zoom in`, `Zoom out`, `Drag to rotate map, click to reset north`) at
  `apps/web/src/components/map-view.tsx:93`, violating the zh-Hant accessible-copy requirement.
  The localized labels `放大地圖` / `縮小地圖` / `重設地圖方向` are applied to
  `aria-label` and `title` after `addControl`, and
  `apps/web/e2e/dashboard.spec.ts:280-282` asserts all three localized control names.

  Re-verification after rebuilding: production build served at `http://127.0.0.1:3002` exposes
  `aria-label` / `title` = `放大地圖`, `縮小地圖`, `重設地圖方向` (probe
  `/tmp/ctrl-probe.mjs`). The earlier production artifact predated the label edit; the stale
  build was the source of the English DOM text.

## Evidence reviewed

- Unit: 3 files / 58 tests PASS.
- Typecheck, lint, production build PASS (Next.js 16.4.2).
- Dashboard e2e: 5/5 PASS, including the localized control-name assertions.
- Browser: zh-Hant metadata, glossed tokens, Chinese layer copy over an English API payload,
  synthetic preview `可重現執行完成 · 種子 42`, zero console errors.

## Limits

- Synthetic fixture data only; no authoritative observation dataset or importer.
- Machine-readable/provenance values remain English by design per the spec.
