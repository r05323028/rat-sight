# Adversarial review

**Reviewer:** verification-reviewer
**Decision:** PASS after clarification

Findings and resolutions:

- **AR-LAW-001 — MAJOR — RESOLVED:** HMR rejection was not treated as sufficient hydration proof. Design now requires fresh-browser hydration and expected API-request evidence, with explicit host/origin alignment.
- **AR-LAW-002 — MAJOR — RESOLVED:** Taipei conversion now has an exact UTC example, machine-timezone independence, equal-boundary inclusion, and reversed-range validation requirements.
- **AR-LAW-003 — MAJOR — RESOLVED:** The change does not add a count endpoint or total field. UI reports returned count only and warns when `truncated` means additional matching records exist.
- **AR-LAW-004 — MEDIUM — RESOLVED:** Layer count is defined as visible rows exactly once; supported layers get visibility controls, unsupported entries get status text without checkboxes, and the dedicated stormwater row is preserved.
- **AR-LAW-005 — MEDIUM — RESOLVED:** Design names API/web ports, CORS/API environment, browser origin, health check, API interaction check, and free-port/ownership checks.

Residual risk: authoritative datasets and real administrative decision workflows remain outside scope; synthetic fixtures must remain visibly `SIMULATED`.
