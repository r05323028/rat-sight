# Proposal

## Why

RatSight's first-run workspace currently presents all dashboard copy in English while its
intended municipal audience reads Traditional Chinese. The reading load is highest exactly
where the product must be most careful: synthetic-data boundaries, empty and error states,
provenance, and scientific classifications. A single-locale Traditional Chinese interface
removes that mismatch without changing any data, API contract, or scientific claim.

## What Changes

- Translate all user-facing web copy in the dashboard, map region label, and document
  metadata to Traditional Chinese (zh-Hant). No language switcher and no i18n library.
- Preserve the canonical classification tokens `OBSERVED`, `INFERRED`, `SIMULATED`, and
  `UNVERIFIED` verbatim and pair them with a Traditional Chinese gloss.
- Keep machine-readable values (IDs, versions, URLs, hashes, licenses, CRS, publisher
  attributes) exactly as provided.
- Update component and end-to-end assertions to the new copy.

## Out of Scope

Bilingual switching, translating backend payloads, translating repository documentation,
new fonts or dependencies, and any change to datasets, models, API contracts, or scientific
claims.
