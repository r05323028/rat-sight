# Spec Delta

## ADDED Requirements

### Requirement: Traditional Chinese interface copy

All user-facing text in the web application MUST be written in Traditional Chinese
(zh-Hant), including headings, controls, statuses, empty/error states, provenance field
labels, help notes, and accessible names.

#### Scenario: Analyst opens the dashboard

- **WHEN** a user loads the dashboard
- **THEN** every static label, control, status, and help note is Traditional Chinese, and the document language is `zh-Hant`

#### Scenario: Service states

- **WHEN** a catalog, boundary, stormwater, rodent-report, or preview request is loading, empty, unavailable, or failing
- **THEN** the message is Traditional Chinese and still distinguishes loading, empty, unavailable, and error states from each other

### Requirement: Canonical scientific tokens preserved

The tokens `OBSERVED`, `INFERRED`, `SIMULATED`, and `UNVERIFIED` MUST remain visible
verbatim and MUST be paired with a Traditional Chinese gloss. Localization MUST NOT merge,
rename, or reclassify them.

#### Scenario: Simulated preview

- **WHEN** simulated preview output or the synthetic fixture layer is shown
- **THEN** the `SIMULATED` token appears with a Chinese gloss and the copy still states that the output is synthetic and not observed movement

### Requirement: Machine-readable values remain verbatim

Identifiers, dataset and resource versions, URLs, hashes, license text, CRS values,
publisher attributes, and API-provided values MUST NOT be translated or rewritten.

#### Scenario: Provenance block

- **WHEN** provenance is displayed
- **THEN** field labels are Traditional Chinese while source URLs, dataset IDs, hashes, licenses, and CRS strings remain exactly as provided

### Requirement: Traditional Chinese document metadata

The document language and page metadata MUST identify Traditional Chinese.

#### Scenario: Browser loads the page

- **WHEN** the page is served
- **THEN** `<html lang="zh-Hant">`, the title, and the description are Traditional Chinese
