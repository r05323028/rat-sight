# Proposal

## Why

The first black-box review showed that RatSight's synthetic demo is understandable but empty official layers lack next steps, simulation output can resemble analysis, and date filtering is hard to interpret. The required initial municipal evaluation was repeated against the current runtime and was BLOCKED because `http://localhost:3000` serves North and redirects to `/login`; no RatSight workflow could be assessed in that runtime.

Evidence: `docs/rat-sight-first-black-box-usability-review.md`; initial evaluation report from `verification.municipal-analyst@rat-team`; current runtime curl evidence.

## What Changes

- Improve dashboard dataset status and empty-state guidance without fabricating data.
- Separate available, unavailable/planned, loading, error, viewport-suppressed, and filtered-empty states.
- Make implemented official reference, synthetic report, synthetic simulation, and planned layers distinct.
- Make synthetic simulation limitations prominent before and after execution.
- Make UTC date-range semantics and filtered counts explicit.
- Add one safe, documented local setup path using existing importers only.

## Non-goals

No new datasets, risk scoring, simulation model, ETL framework, auth change, architecture rewrite, or third-party UI dependency.
