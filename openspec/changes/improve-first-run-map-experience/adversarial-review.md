# Adversarial Review

**Decision: PASS WITH IMPLEMENTATION CONDITIONS**

- AR-001 (BLOCKING): Do not weaken bbox protection or turn unavailable data into zero. **RESOLVED by design/spec.**
- AR-002 (MAJOR): Simulation wording must remain adjacent to result metrics and preserve seed/parameters. **RESOLVED by design/spec.**
- AR-003 (MAJOR): Runtime currently serves North `/login`; browser acceptance is blocked until a RatSight runtime is restored. **OPEN environmental limitation; implementation may proceed, but final populated/browser acceptance cannot claim PASS.**
- AR-004 (MAJOR): No source/importer/API contract change may fabricate official data. **RESOLVED by scope.**

Implementation must add focused UI tests and preserve existing contracts. Final QA must record the runtime blocker precisely if unresolved.
