# Design

1. Translate the existing inline copy in `apps/web/src/components/dashboard.tsx`,
   the map region accessible name in `apps/web/src/components/map-view.tsx`, and the
   document metadata in `apps/web/src/app/layout.tsx`. This is a single-locale build:
   no language switcher, message catalog dependency, or locale routing is added.
2. Keep layer labels consistent with the API. The frontend fallback catalog uses
   Traditional Chinese labels; known layer ids map to Chinese labels when the API returns
   English labels, while unknown ids fall back to the API-provided label so nothing is
   invented. Layer availability, classification, and provenance semantics do not change.
3. Classification badges keep the canonical token first with a Chinese gloss after it
   (`SIMULATED · 模擬`, `UNVERIFIED · 未驗證`). Labels derived from backend data keep their
   tokens; only presentation text is translated.
4. Provenance and detail blocks translate field labels only. Source URLs, dataset and
   resource versions, hashes, licenses, attribution, CRS, and publisher attribute values
   stay byte-identical.
5. Update `apps/web/src/components/dashboard.test.tsx`, `apps/web/src/components/map-view.test.tsx`,
   and the e2e specs that assert UI copy. API fixture payloads stay English because they
   model backend data, not interface text.
6. Verify with focused web tests, typecheck, lint, build, and a browser pass over the
   dashboard states (catalog available/unavailable, synthetic preview, empty datasets)
   using existing mock/isolated runtimes.

## Decisions

- Inline copy over a message catalog: one locale, no runtime switching requirement, so a
  catalog would add indirection without a consumer.
- Token plus gloss over translated-only status: keeps scientific vocabulary identical to
  storage and API while remaining readable in Chinese.
- API-provided values are never translated, even when they read like prose, because they
  are evidence payloads rather than interface text.

## Evidence and limits

This change is presentational. It does not add data, alter classifications, or change query
semantics. Authoritative-data acceptance and bilingual switching remain out of scope.
