# Tasks

- [x] 1. Record and reconcile the verified Taipei administrative-boundary source in `docs/infrastructure/data-sources.md`, preserving the candidate policy for other sources.
- [x] 2. Pin reuse compatibility to the archived implementation, endpoint, provenance envelope, CRS, and classification boundary.
- [x] 3. Add an isolated, deterministic real FastAPI + Next.js smoke harness with migration, seed, readiness, no API interception, assertions, and cleanup.
- [x] 4. Add focused smoke assertions for available and empty administrative-layer states and visible provenance; retain existing hermetic UI tests.
- [x] 5. Run independent code review on the actual source, harness, and test diff.
- [x] 6. Run QA, full relevant tests, traceability validation, and the OpenSpec quality gate.
- [x] 7. Give each smoke run a unique Compose project and restrict destructive teardown to its own started stack.
- [x] 8. Pin smoke database settings and derive the API connection URL from the same settings.
- [x] 9. Assert the populated API response contains EPSG:4326-compatible longitude and latitude coordinates.
- [x] 10. Re-run focused checks and update verification evidence for these corrective fixes.
