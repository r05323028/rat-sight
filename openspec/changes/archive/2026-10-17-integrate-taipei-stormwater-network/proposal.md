# Proposal

## Why

RatSight has an official administrative reference layer and synthetic simulation preview, but no inspectable infrastructure reference layer. The Taipei Public Works Department stormwater-system utility XML is the best MVP candidate among the investigated official alternatives because it declares EPSG:3826 and provides structured utility attributes, while explicitly warning that the map is reference-only.

Evidence: `EVID-TPE-STORMWATER-NETWORK-2026-10-16` in `docs/evidence/taipei-stormwater-network-2026-10-16.md`.

## What Changes

- Add a local-source-file-only, checksum-verified importer for Candidate B's XML/GML stormwater resource; downloading is explicitly outside the importer.
- Add additive PostGIS persistence and a versioned GeoJSON API for stormwater reference lines.
- Add a distinct dashboard layer with visibility, loading/empty/error states, pipeline selection, source attributes, and provenance.
- Filter synthetic visualization to edges with positive visits without changing simulation math.
- Perform one-time isolated verification of the existing official Taipei district archive, without adding government downloads to regular tests.

## Scope and Integrity Boundary

Stormwater lines are infrastructure reference data, not rodent observations, inferred connectivity, traversability, movement weights, or risk predictions. Endpoint fields are retained as source attributes only; no topology is reconstructed. Raw official files remain outside Git. No synchronization, vector tiles, generic ETL, or simulation integration is introduced.
