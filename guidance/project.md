# Project guidance

Purpose: evidence-driven urban rodent movement simulation and municipal decision support for Taipei. This repository is only a development foundation.

Interfaces: dashboard → FastAPI JSON → application/domain services; geo and simulation remain independent Python packages. Keep CRS explicit (`EPSG:4326`, `EPSG:3826`). Track provenance/classification at boundaries.

Before changing a public contract or model assumption, update OpenSpec, document compatibility, add tests and request review. Synthetic geometry/output must retain `SIMULATED` status. No database reset or fabricated real-world statistic.

OpenRig coordination uses only supported queue/gateway/terminal workflows. Human decisions require explicit approval.
