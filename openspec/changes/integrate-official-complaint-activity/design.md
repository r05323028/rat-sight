# Design

## Feasibility gate

Implementation is blocked until the official dataset and applicable reuse terms are verified, the actual CSV structure and record grain are understood, and exact official category values defensibly identify rodent-related complaints. A category such as pest control or 病媒 is not rodent-specific without source evidence. The feasibility artifact must record canonical URLs, resource IDs, verification date, encoding, date semantics, category values, duplicate/missing behavior, coverage, and update history.

## Conditional contract

Only after GO, persist monthly aggregates of explicitly qualified official categories. Required dimensions are month, original official category, count, dataset/resource identity, resource version, data classification, and provenance. Preserve original category terminology and distinguish complaint, observation, inspection, treatment, and confirmation.

No raw CSV, names, contacts, descriptions, attachments, or complaint IDs may be committed, persisted, or exposed. Unknown license/privacy/schema/record-grain values block implementation. No geographic filtering or incident-location claims are allowed unless verified source fields support them.

## Conditional implementation boundary

A future local importer accepts an explicitly supplied official CSV, verifies source identity/license, validates required fields/categories/dates, applies an exact documented category allowlist, handles verified duplicate grain, supports dry-run, records exclusions, and commits idempotently without partial writes. The API exposes only monthly aggregates and provenance, with unavailable/empty/filtered-empty/error states. The UI is a simple historical trend with explicit limitations. No scheduler, generic ETL, plugin framework, charting dependency, or simulation connection is introduced.
