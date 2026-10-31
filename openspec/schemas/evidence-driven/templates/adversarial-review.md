# Adversarial Review

Complete before `tasks.md`, and run `make openspec-preflight CHANGE=<change>` before the first
implementation edit. A blocked preflight blocks implementation until the recorded state is fixed.

Challenge assumptions, requirements, design, evidence, scientific validity, and failure cases.
Record findings, rationale, and resolutions in prose; no prescribed headings or table format.

## Review repository context, not only the change directory

Read the code and specifications the change touches before judging it. At minimum:

- Existing capabilities under `openspec/specs/` that already constrain this behavior, and whether
  this change duplicates or contradicts them.
- The modules, entry points, and shared types the change will modify, plus their callers.
- Cross-module contracts: function signatures, request/response shapes, database columns,
  configuration keys, and file formats that other code already depends on.
- Historical assumptions recorded in `docs/decisions/`, `docs/evidence/`, and earlier changes that
  remain binding.

Reference those paths in prose. Do not copy repository knowledge into a new artifact: point at the
file you read.

## What to attack

- Behavior that changes, not only files that change. State the observable before/after for each.
- Callers and consumers that were not considered, and contracts whose meaning shifts.
- Implicit invariants the change relies on but does not restate (ordering, units, CRS, encoding,
  nullability, idempotency, authorization, provenance).
- Predicted impact versus the implementation you expect: what will actually be touched, and what
  the author believes will not.
- Paths that will remain untested, including negative and boundary cases.
- Unsupported claims: completion, accuracy, performance, or scientific validity asserted without
  evidence that could be checked.

## Findings

Each finding in `verification/gate.json` carries three independent axes:

- `severity`: `BLOCKING`, `MAJOR`, `MINOR`, or `INFO` — how much it matters.
- `verification`: `VERIFIED`, `SUSPECTED`, `UNVERIFIED`, or `JUDGMENT` — how well you established
  that the issue is real. Use `JUDGMENT` for concerns only a human can settle.
- `status`: `OPEN`, `RESOLVED`, `ACCEPTED_RISK`, or `DEFERRED` — what was decided about it.

A `BLOCKING` finding must record `evidence`: the reproduction, the failing test, the exact
contradiction, or the file and line you read. A non-empty evidence field is a claim the gate cannot
verify; write it so another person could check it. Blocking findings cannot be waived. A
non-blocking `ACCEPTED_RISK` needs human approval tied to the exact finding ID and a recorded
`residual_risk`.

Keep findings concise and evidence-supported. Do not pad the review with an inventory of everything
you read; the gate requires this report and validates recorded review state, not its length.
