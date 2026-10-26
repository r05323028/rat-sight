# Code review

Decision: PASS with documented limitations.

Independent review confirmed:

- Pinned OSM source hash and provenance are validated.
- Graph uses shared OSM nodes only; source bends survive in edge geometry.
- Directed edge IDs are unique, including reverse edges.
- Invalid movement weights propagate; only no-eligible transitions terminate early.
- API exposes bounded trajectories, geometry, truncation, provenance, and SIMULATED classifications.
- MapLibre renders API geometry directly for source-network edges.
- Synthetic graph remains available and endpoint fallback is limited to that fixture.
- UI communicates early termination, trajectory truncation, uncalibrated weights, no observed movement, and no risk claim.

Verification: targeted pytest 14 passed; Vitest 61 passed; TypeScript, ESLint, Ruff, and basedpyright clean. QA verified 117 nodes, 249 directed edges, 73 bent edges, deterministic 40-seed output, and zero geometry mismatches. Municipal Analyst verified study-area selection, run flow, labels, provenance, and aggregate/trajectory separation. Pixel-level basemap alignment was not independently verified.

Known limits: source covers a 0.004° Songshan bbox, not Taipei City; OSM streets are a spatial modeling assumption, not rodent evidence; Rat Radar remains NO-GO; stormwater remains reference-only; no underground traversal.
