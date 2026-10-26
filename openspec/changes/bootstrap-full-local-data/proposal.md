# Proposal

## Why

RatSight currently has verified official Taipei reference importers, but local operators must manually obtain raw archives and invoke each importer. A dedicated persistent local profile should make supported reference layers available across API/Web restarts without touching shared development resources.

## What Changes

- Add a project-scoped persistent PostGIS profile for the verified administrative-boundary and stormwater sources.
- Add a repeatable `make data-bootstrap PROFILE=full-local` command with inspect-only/dry-run support, pinned source verification, migrations, imports, and an inventory summary.
- Keep raw licensed archives outside Git and fail closed when files, hashes, CRS, geometry, or source identity do not match documented pins.
- Make synthetic rodent fixtures opt-in and visibly `SIMULATED`.
- Document restart, idempotency, ownership-safe teardown, and populated-browser verification.
- Assess candidate sewer/manhole/trash-bin layers without ingesting unresolved sources.

## Integrity Boundary

Administrative boundaries remain `ADMINISTRATIVE_REFERENCE`/`UNVERIFIED`; stormwater remains `INFRASTRUCTURE_REFERENCE`/`UNVERIFIED`; synthetic reports remain `RODENT_REPORT`/`SIMULATED`. Geometry does not establish connectivity, traversability, rodent movement, risk, prevalence, or intervention effect. No real citizen reports are ingested.

## Human decision boundary

Use only the already verified source identities and licenses in project evidence. Any changed source hash, unresolved ownership, new dataset, or material architecture/scientific assumption stops for human review.
