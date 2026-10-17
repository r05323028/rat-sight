# Evidence: Taipei rodent-report source investigation (2026-10-17)

## Scope and classification

This is a source-discovery record, not an ingestion or validation record. All external candidates below are `UNVERIFIED` for RatSight use unless explicitly stated otherwise. No citizen report rows, photographs, CSV payloads, or personal data were downloaded or copied into this repository. The observed website claims are source-interface observations, not RatSight `OBSERVED` rodent records.

The investigation was limited to public landing pages, rendered metadata, and response headers. It did not bypass access controls, scrape report rows, or invoke an export download.

## Candidate A — Rat Radar / 見鼠雷達 (`ratdar.taipei`)

- **Publisher/ownership:** The site's transparency page describes the service as a citizen-initiated public-information project and states that it is公益/non-profit. This is a self-description; no Taipei City Government ownership or endorsement was established.
- **URLs checked:** <https://ratdar.taipei/>, <https://ratdar.taipei/reports>, <https://ratdar.taipei/stats>, <https://ratdar.taipei/transparency>, and the linked export endpoint <https://ratdar.taipei/reports/export>.
- **Access and format:** Public HTML pages are accessible without login. The export endpoint advertises `text/csv` and a dated attachment filename in an HTTP `HEAD` response (2026-10-17); the CSV itself was deliberately not downloaded. The public pages are server-rendered and expose no documented stable API/schema in the material checked.
- **Visible fields/semantics:** The report-list page labels columns as report time, type, location, status, photo, and description. It exposes a status filter labelled `已通報1999` (reported to 1999), so this is a submitter/status assertion, not evidence that a municipal 1999 case was independently confirmed. The page separately displays pending review items and warns they are unverified and must not be treated as confirmed rodent-problem locations.
- **Review process claimed by publisher:** The transparency page says submissions contain a photo, location, and description; AI screening and volunteer human review precede public display. It describes public display as approved material, but the page does not establish sensitivity/specificity, inter-reviewer agreement, species validation, or a municipal confirmation process.
- **Privacy and redistribution:** The landing page announces a privacy switch controlling whether a submitter's personal data appears in rankings and mentions photos/names. Public report pages expose photographs and location/description presentation, and the export route exists. No machine-readable license, data-processing agreement, retention policy, coordinate precision policy, or redistribution permission was found in the checked pages. This is a blocker for raw ingestion or redistribution until the publisher gives written authorization and a field-level privacy specification.
- **Spatial/temporal coverage:** The site presents itself as Taipei rodent reporting and displays a map/list, but the checked pages do not provide a formal coverage definition, coordinate CRS, geocoding accuracy, historical retention policy, or completeness statement. Treat coverage and location precision as unknown.
- **Quality/limitations:** Reports are opportunistic citizen submissions and therefore subject to reporting access, awareness, duplicate, geolocation, photo-selection, moderation, and temporal biases. “Approved” is a platform moderation state, not a standardized field observation or municipal infestation confirmation. The platform's own aggregate/statistics pages are descriptive platform outputs and must not be interpreted as prevalence, incidence, or causal evidence.
- **MVP recommendation:** Do **not** ingest raw reports, photos, names, exact coordinates, or the public CSV. First obtain publisher authorization, license/terms, privacy/retention and security requirements, schema/data dictionary, CRS/geocoding details, moderation-state definitions, duplicate policy, update contract, and a permitted de-identified extract. If approved, start with an aggregate or coarse-grid `UNVERIFIED` report layer retaining source URL, retrieval timestamp, publisher status, and uncertainty; do not call it `OBSERVED` or `confirmed` without a defined validation process.

## Candidate B — Taipei City open-data portal

- **Discovery URLs:** <https://data.taipei/> and the portal rules link referenced by existing project infrastructure records: <https://data.taipei/rule>.
- **What was established:** The portal is reachable, and the project already records Taipei open-data as a discovery point. The generic portal landing page alone does not establish that a rodent-report or 1999 complaint dataset is currently published, licensed for this use, complete, or maintained.
- **Search result:** No rodent/1999 dataset was selected or downloaded during this task. A portal search/API contract, dataset identifier, resource version, fields, CRS, update cycle, and license for a relevant dataset remain unverified.
- **Recommendation:** Search only through the portal's documented UI/API after an authorized dataset-selection step. Record dataset ID/resource ID, publisher department, license and attribution, resource version, retrieval timestamp, field semantics, privacy classification, coverage, CRS, and quality notes before any download. A portal listing is not proof that records are public for unrestricted redistribution.

## Candidate C — Taipei 1999 complaint data

- **Candidate discovery URLs:** Taipei City 1999 service entry point is commonly discoverable through Taipei City Government/1999 channels; the generic open-data catalog <https://data.gov.tw/> and Taipei portal <https://data.taipei/> are the appropriate official catalog surfaces checked for discovery. No specific rodent-complaint dataset identifier was established in this investigation.
- **Status:** `UNVERIFIED` candidate only. No endpoint, schema, export, license, CRS, coverage, update cadence, or privacy terms were verified. No complaint records were accessed.
- **Semantic warning:** A 1999 complaint is a service request/report, not necessarily a sighting, inspection finding, treatment action, or confirmed rodent observation. Any future source must preserve these distinctions and any agency status transitions.
- **Recommendation:** Request an official catalog/API record or written data-owner response identifying whether rodent-related complaints are available, at what spatial/temporal resolution, with what aggregation/privacy controls, and under what reuse terms. Prefer agency-provided de-identified aggregates over citizen-level records.

## Other relevant official candidates

The existing project source policy identifies Taipei City Government open data, Taiwan National Land Surveying and Mapping Center, Water Resources Agency, Taipei public-works/sewerage agencies, and environmental/hydrometeorological providers as discovery points. These are contextual or covariate candidates, not rodent observations, unless a source owner documents otherwise. No additional rodent-report source was selected or downloaded here. See `docs/infrastructure/data-sources.md` for the repository's intake requirements (publisher, license, CRS, coverage, privacy, provenance, and update process).

## Evidence, assumptions, and decision boundary

- **Evidence:** Public pages and response metadata were inspected on 2026-10-17. Rat Radar visibly distinguishes pending/unverified reports, exposes report metadata categories, advertises a CSV export, and describes moderation/privacy features.
- **Assumptions:** None about species, reporting completeness, confirmation accuracy, municipal ownership, causal meaning, or representativeness.
- **Model use:** None. These candidates must not supply movement weights, biological parameters, prevalence, or intervention effects.
- **Validation needed:** Data-owner authorization; legal/privacy review; schema and CRS verification; de-identification review; duplicate and moderation-state audit; missingness/coverage assessment; and independent public-health review before any model-facing use.

## Open blockers / return criteria

1. Obtain an authored data-owner/PM decision selecting a source and permitted use.
2. Obtain written license/reuse and privacy/retention terms for any Rat Radar or 1999 extract.
3. Establish field-level semantics (`report`, `sighting`, `moderated`, `municipally confirmed`, `treated`) and preserve them separately.
4. Establish spatial precision/CRS and permitted aggregation before storage.
5. Do not create an ingestion implementation under this Phase A qitem.
