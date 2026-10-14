# Data policy

No Taipei observations or infrastructure datasets are bundled or downloaded during initialization. `raw/` is immutable intake, `processed/` contains reproducible derived outputs, and `fixtures/` contains clearly synthetic test/demo data only.

Every future dataset must record source URL, retrieval time, license, CRS, coverage, processing steps, and classification (`OBSERVED`, `INFERRED`, `SIMULATED`, or `UNVERIFIED`). Never place credentials or private municipal data here.
