# Candidate data sources and intake policy

No source below has been downloaded or certified for this project. Treat these as candidates only; verify current publisher, license, terms, CRS, schema, coverage, update cadence and permitted use before ingestion.

Potential discovery points include Taipei City Government open-data portal (`data.taipei`) for municipal layers; Taiwan National Land Surveying and Mapping Center for authoritative base mapping; Water Resources Agency and Taipei city public-works/sewerage agencies for drainage/sewer records; and official environmental/hydrometeorological providers for weather and environmental covariates. Source ownership, public access and dataset availability must be checked per layer.

For each candidate, record contact/endpoint, license and attribution, retrieval date, date range, coordinate precision, CRS, geometry validity, missingness, observation-vs-administrative meaning, privacy sensitivity and update process. Do not infer sewer connectivity from surface geometry. Do not fetch bulk data during project initialization.

Raw inputs are immutable. Derived data must be reproducible from versioned processing code and provenance records. Every feature/result carries its evidence classification. Human-sourced sightings require privacy and retention review before any real ingestion.
