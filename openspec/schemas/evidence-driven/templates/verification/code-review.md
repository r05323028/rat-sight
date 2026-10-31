# Code Review

After implementation, inspect the actual diff **and the code around it**. The diff shows what moved;
it does not show what depends on it.

## Required content

1. **Changed behavior** — for each behavior the change alters, the observable before and after.
   "Renamed a function" is not a behavior; "empty input now returns `null` instead of throwing" is.
2. **Callers, consumers, and shared contracts** — who calls the changed code, what they assume, and
   whether those assumptions still hold. Check signature, request/response shape, database column,
   configuration key, CRS/unit, encoding, ordering, and nullability changes.
3. **Implicit invariants** — properties the code relied on without stating them (idempotency,
   authorization, transaction boundaries, cache keys, file layout). Say whether each still holds.
4. **Unintended side effects** — behavior that changed outside the stated scope, including logging,
   error messages, performance characteristics, and data written to disk or a database.
5. **Untested affected paths** — paths the change touches that no test exercises, including negative
   and boundary cases. Name them; do not imply coverage that does not exist.
6. **Predicted versus actual impact** — compare the impact the proposal and design predicted with
   what the diff actually touched. Call out anything that appeared or disappeared.

Use repository tooling (search, call graphs, type checkers, test runners) where available; cite what
you used. Do not rely on the implementation summary as evidence.

## Findings

Put decision state and finding IDs, severity, verification, and status in
`verification/gate.json` using the same three axes as the adversarial review: `severity`,
`verification` (`VERIFIED`, `SUSPECTED`, `UNVERIFIED`, `JUDGMENT`), and `status`. A `BLOCKING`
finding must record `evidence`.

The quality gate requires this report and validates recorded review state. It does not inspect the
prose, confirm that the change was executed, or prove that downstream consumers were exercised.
