# Geospatial Data Layers Specification

## Purpose
Make the existing Taipei administrative boundary vertical slice the first verified real-world geospatial data layer while preserving provenance and classification boundaries.

## Requirements

### Requirement: Verified geospatial source registry
The project MUST document the selected official Taipei administrative-boundary source with its publisher, source and download URLs, format, CRS, geographic coverage, license, archive identity, retrieval evidence, processing target CRS, and known limitations. The source resource version is 2022-09-15 and post-version currentness MUST remain explicitly `UNVERIFIED`; no synthetic fixture may be described as the official source.

#### Scenario: Source record is reviewed
- **WHEN** a maintainer reviews the data-source registry
- **THEN** the registry links the evidence record and distinguishes verified facts from unresolved currentness or other limitations

### Requirement: End-to-end administrative layer smoke
The project MUST provide a reproducible smoke test that exercises a running frontend and FastAPI application together for the administrative district layer without intercepting the administrative-district API response in the browser. The smoke MUST verify a valid available FeatureCollection, `data_class=ADMINISTRATIVE_REFERENCE`, district identity, and visible provenance while leaving synthetic simulation behavior independent.

#### Scenario: Populated application path
- **WHEN** the application is started with a deterministic populated administrative-district store
- **THEN** the browser obtains the boundary response from the running FastAPI endpoint, renders the administrative layer controls, and exposes district identity and provenance to the user

#### Scenario: Missing application data
- **WHEN** the running API has no imported administrative districts
- **THEN** the API returns an explicit empty state and the dashboard shows no fabricated geometry or rodent interpretation
