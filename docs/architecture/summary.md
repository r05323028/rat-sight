# RatSight research and development principles

Project boundaries are deliberately modest: local dashboard + FastAPI + two independent Python packages + PostgreSQL/PostGIS. No brokers, caches, distributed services, graph DB or ML pipeline.

Data classes are `OBSERVED`, `INFERRED`, `SIMULATED`, `UNVERIFIED`; preserve provenance, assumptions and model metadata. No synthetic demo may be described as a real route or risk assessment.

The API currently provides health/status, layer catalog, model catalog and deterministic synthetic preview. The only initial model is a weighted random walk over a tiny synthetic graph. It has no calibration, biological validity, predictive skill or municipal intervention efficacy.

Develop via tests and review. Treat dataset candidates as unverified until licensing, CRS, completeness and provenance are checked. Human approval required for major architecture or scientific assumption changes.
