# Architecture overview

RatSight is a monorepo with four independently testable layers. The browser dashboard calls a single FastAPI service; the service owns HTTP contracts and persistence integration; `ratsight-geo` owns CRS/geometry operations; `ratsight-simulation` owns graph-based mathematics and has no web-framework dependency. PostgreSQL/PostGIS is the sole development service.

```text
Next.js + MapLibre + TanStack Query
                │ HTTP /api/v1
                ▼
FastAPI routes → application service → domain/API schemas
                         │                    │
                         ▼                    ▼
                   SQLAlchemy/PostGIS   simulation package
                                              │
                              geo package ────┘ (future composition)
```

## Initialization vertical slice

`POST /api/v1/simulations/preview` runs a deterministic weighted random walk over a small synthetic NetworkX graph. Response includes status `SIMULATED`, model/version, parameters, seed, synthetic provenance, assumptions, node/edge visitation counts and normalized frequencies. It is a demonstration, not a prediction. Coordinates are schematic fixture geometry, not infrastructure or observation data.

The UI starts on a configurable CARTO Positron style (`NEXT_PUBLIC_MAP_STYLE_URL`), with provider attribution retained. The Taipei administrative district and stormwater pipeline layers are available through local-file-only importers and versioned GeoJSON APIs. Stormwater is `INFRASTRUCTURE_REFERENCE` / `UNVERIFIED`; it is not rodent evidence and its publisher endpoint attributes do not establish physical connectivity. Other non-synthetic data layers remain unavailable placeholders. Map style/network availability depends on provider terms and connectivity.

## Boundaries and contracts

- `apps/web` consumes versioned JSON contracts; it does not import Python code.
- `services/api` translates Pydantic requests/responses and calls simulation/domain code; domain math stays outside FastAPI.
- `packages/geo` supports EPSG:4326 and EPSG:3826 explicitly; source CRS must be provided rather than guessed.
- `packages/simulation` depends on NetworkX/NumPy/SciPy only; seed and model metadata travel with every result.
- API persistence uses SQLAlchemy/Alembic and a PostGIS geometry column. Startup does not require a database; health is liveness, status reports DB availability.

## Evidence classification

`OBSERVED`: direct, documented field observation with source/method. `INFERRED`: data-derived result with explicit assumptions. `SIMULATED`: model-generated output with model version, parameters, seed, provenance, assumptions and status. `UNVERIFIED`: unsupported hypothesis. Never draw or label a simulated path as observed animal movement.
