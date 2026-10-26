# Adversarial review

Change: `localize-web-traditional-chinese`. Reviewer: `verification-reviewer@rat-team`
(independent seat, read-only), via OpenRig queue items.

## Round 1 — `qitem-20261023071857-1b0d0022fcd3e2a4`

`DECISION: CHANGES-REQUESTED`

- **AR-L10N-001 — MAJOR — RESOLVED.** Review was taken before the translation landed; the tree
  then still rendered English interface copy. Resolved by the zh-Hant implementation across
  `apps/web/src/components/dashboard.tsx`, `apps/web/src/components/map-view.tsx`, and
  `apps/web/src/app/layout.tsx`.

## Round 2 — `qitem-20261023073428-e573ff9152909007`

`DECISION: CHANGES-REQUESTED`

- **AR-L10N-002 — MEDIUM — RESOLVED.**
  (a) Unknown API layer ids fell back to raw English `layer.label`; `renderCatalogLayer` now uses
  `LAYER_LABEL_OVERRIDES[layer.id] ?? "未命名資料圖層"`.
  (b) Available catalog classifications rendered raw tokens without a Chinese gloss; catalog rows,
  selected district details, and selected stormwater segment details now pass through
  `CLASSIFICATION_LABELS` (`OBSERVED · 已觀測`, `INFERRED · 推論`, `SIMULATED · 模擬`,
  `UNVERIFIED · 未驗證`).
- Regression test added: `apps/web/src/components/dashboard.test.tsx`
  "never leaks an unknown API label and glosses classifications".

## Round 3 — `qitem-20261023073726-84868bfc2a25188f`

`DECISION: PASS` — AR-L10N-002 confirmed resolved; no further findings.

## Verification cited by the review

- Unit: 3 files / 58 tests PASS.
- Typecheck, lint, production build PASS (Next.js 16.4.2).
- Dashboard e2e: 5/5 PASS.
- Browser: zh-Hant metadata, glossed tokens, Chinese layer copy from an English API payload,
  synthetic preview `可重現執行完成 · 種子 42`, no console errors; screenshot
  `/tmp/ratsight-l10n-zh-final.png`.

## Limits

- Review and runtime evidence cover synthetic fixture data only; no authoritative observation
  dataset or importer exists.
- Machine-readable/provenance values remain English by design; the review did not treat that as an
  interface-copy defect.
