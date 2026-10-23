# Proposal

## Why

RatSight's isolated browser runtime works, but the default development path can serve HTML while failing React hydration when a browser reaches it through `127.0.0.1`: Next blocks the HMR cross-origin request. The dashboard also asks Taiwan analysts to enter UTC, exposes ambiguous layer counts/disabled controls, and can make truncated report results look complete.

This change will make one local launch path reproducible, add the minimal Next dev-origin configuration, accept Asia/Taipei date-time input while preserving the existing UTC API contract, clarify layer control/count semantics, and qualify returned/truncated report counts. No backend contract, dataset, model, authentication, or shared runtime ownership changes.

Canonical launch evidence will use explicit ownership checks, `CORS_ORIGINS=http://127.0.0.1:3010` and `NEXT_PUBLIC_API_URL=http://127.0.0.1:8010`, API port `8010`, web port `3010`, browser origin `http://127.0.0.1:3010`, and health/API interaction checks. Ports are examples, not universal requirements; a free-port check is mandatory before launch.

## What Changes

- Runtime launch/configuration and documentation only where needed to reproduce a working local app.
- Dashboard date conversion, layer semantics, report count/truncation wording, and focused tests.
- Real-browser verification using synthetic fixtures only.

## Out of Scope

Authoritative data ingestion, new endpoints/count queries, risk models, scientific claims, authentication, process termination for unrelated projects, and changes to `improve-first-run-map-experience`.
