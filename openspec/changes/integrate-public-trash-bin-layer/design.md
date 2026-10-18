# Design

## Feasibility gate

Current decision is **conditional NO-GO for implementation**: publisher CRS/axis order is absent, so WGS84-looking coordinates must not be assigned EPSG:4326. Implementation requires verified source identity/license, resource relationship, CRS, valid point mapping, deterministic facility identity, duplicate/overlap policy, and a useful valid record set. Raw source files remain outside Git; every imported resource requires retrieval date, exact byte count, SHA-256, resource version, and provenance.

## Conditional contract

Use one authoritative resource for MVP, but no resource is selected under the current conditional NO-GO. Store only approved facility attributes, source identity, provenance, and EPSG:4326 Point geometry only after CRS confirmation. If no official identifier exists, derive a deterministic source-scoped identity and label it as generated, never as an official facility ID. Canonicalize CP950-decoded fields to UTF-8, apply Unicode NFC, preserve field order, use length-prefixed field bytes with explicit field count, preserve coordinate lexical text until strict numeric validation, and hash dataset ID, resource ID, and canonical row with SHA-256. Reject malformed encodings and canonicalization collisions; fixture tests must prove repeatability. Classification remains environmental/public-cleanliness reference data and `UNVERIFIED` where currentness or geometry accuracy is not confirmed.

## Human decision boundary

The human project owner must select Resource A or Resource B, or explicitly keep both as separate future layers, after CRS/axis, license, currentness, privacy, and coverage decisions. A future implementation may not silently union the resources.

## Conditional vertical slice

A local importer validates encoding, required columns, CRS, finite coordinates, geometry ranges, duplicates, and source hash; supports dry-run, transactional idempotent persistence, and counts/rejection reasons. A bounded `/api/v1/public-trash-bins` endpoint returns EPSG:4326 GeoJSON with bbox filtering and explicit data states. Dashboard uses an optional MapLibre point layer, bounded inspection list, point selection, provenance, attribution, and limitations. No generic ETL, scheduler, clustering, risk scoring, or simulation integration.
