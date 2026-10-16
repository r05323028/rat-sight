# Candidate data sources and intake policy

Sources not listed in the verified record below remain candidates only; verify current publisher, license, terms, CRS, schema, coverage, update cadence and permitted use before ingestion.

## Verified administrative reference: Taipei district boundaries

- Evidence ID: `EVID-TPE-DISTRICT-BOUNDARIES-2026-10-15`
- Publisher: Taipei City Civil Affairs Bureau (`臺北市政府民政局`)
- Dataset: `121199`, resource `臺北市區界圖_20220915`, resource version `2022-09-15`
- Metadata: https://data.taipei/dataset/detail?id=1601ef3a-c253-4988-b047-943d9e786143
- Canonical catalog: https://data.gov.tw/dataset/121199
- Download archive: https://data.taipei/api/dataset/1601ef3a-c253-4988-b047-943d9e786143/resource/d8b7eb29-136f-49fc-b14b-3489d3656122/download
- Format and coverage: SHP archive containing Taipei City's 12 administrative districts; source CRS `EPSG:3826` (TWD97), transformed to `EPSG:4326` for the API.
- License: Government Open Data License v1 (`政府資料開放授權條款-第1版`); attribution is retained in provenance.
- Archive SHA-256: `77bcc347b503b8ff8a43f7e1afaaedb18877a6222282587b145adaba69afd2d9`.
- Classification: `data_class=ADMINISTRATIVE_REFERENCE`; this is geographic context, not a rodent observation or simulation. The implementation retains `classification=UNVERIFIED` because currentness after the 2022-09-15 resource version was not established.
- Limitations: archive retrieval/hash and 12-feature inspection are recorded in the evidence file; no live synchronization is implied. Raw licensed input is not committed; import is archive-only and reproducible from the documented source.

Potential discovery points include Taipei City Government open-data portal (`data.taipei`) for other municipal layers; Taiwan National Land Surveying and Mapping Center for authoritative base mapping; Water Resources Agency and Taipei city public-works/sewerage agencies for drainage/sewer records; and official environmental/hydrometeorological providers for weather and environmental covariates. Source ownership, public access and dataset availability must be checked per layer.

For each candidate, record contact/endpoint, license and attribution, retrieval date, date range, coordinate precision, CRS, geometry validity, missingness, observation-vs-administrative meaning, privacy sensitivity and update process. Do not infer sewer connectivity from surface geometry. Do not fetch bulk data during project initialization.

Raw inputs are immutable. Derived data must be reproducible from versioned processing code and provenance records. Every feature/result carries its evidence classification. Human-sourced sightings require privacy and retention review before any real ingestion.
