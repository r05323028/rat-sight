# RatSight OpenSpec

The project runs OpenSpec with the project-local `evidence-driven` schema
(`openspec/config.yaml` sets `schema: evidence-driven`). The authoritative
lifecycle and checkpoint rules are in `guidance/openspec-workflow.md`; this file
covers the OpenSpec mechanics.

## Schema

`openspec/schemas/evidence-driven/schema.yaml` forks the installed `spec-driven`
schema using only the artifact fields OpenSpec 1.14.1 supports, and adds one
planning artifact:

```text
proposal -> specs -> design -> adversarial-review -> tasks
```

- `adversarial-review` requires `specs` and `design`.
- `tasks` requires `specs`, `design`, and `adversarial-review`.
- `apply` requires `tasks` and tracks `tasks.md`.

The schema enforces artifact presence and ordering only. It does not prove that a
review happened, and the CLI has no post-implementation lifecycle hook, so
independent code review, traceability validation, and human acceptance are
project records, not schema artifacts. Never claim the schema enforces them.

The schema, the workflow in `guidance/openspec-workflow.md`, and the quality gate
are runtime-independent: they need only the OpenSpec CLI, Python 3.10+, and a
repository checkout (the repository's uv environment provides 3.12). Orchestration (who runs a review, how a separate context is
provided, how a human is reached) belongs to the runtime, not to these files.

```sh
openspec schema validate evidence-driven
openspec status --change <change> --json
openspec instructions tasks --change <change>
```

## Change lifecycle

1. `openspec new change <name>` - the project schema is used automatically.
2. Write `proposal.md`, `specs/**/*.md`, `design.md`, and
   `adversarial-review.md` from the templates in
   `openspec/schemas/evidence-driven/templates/`.
3. Resolve every BLOCKING adversarial finding in proposal/specs/design. Only
   then write `tasks.md`, which the schema gates on the review artifact.
4. Implement the tasks and mark checkboxes as work lands.
5. Record the post-implementation stages inside the change directory:
   `verification/code-review.md`, `verification/traceability.md`, and, when
   required, `verification/acceptance.md`. Start each record from the matching
   template in `openspec/schemas/evidence-driven/templates/verification/`.

## Quality gate

```sh
make openspec-gate CHANGE=<change>      # python3 scripts/openspec_quality_gate.py <change>
make openspec-archive CHANGE=<change>   # gate first, archive only if it passes
```

Exit `0` passes, `1` blocks, `2` is a usage error; `--json` prints the report.
The gate re-reads the planning artifacts, the `verification/` records, and the
OpenSpec CLI's own validation, and it checks recorded evidence rather than file
existence, checked boxes, or agent summaries. Fix the evidence, never the
report. Archive through `make openspec-archive` (or an equivalent gate run
followed by `openspec archive`): `openspec archive` on its own does not consult
the gate.

## Evidence and classification

Evidence belongs in `docs/evidence/`; cite stable evidence IDs and parameter IDs
in specs and designs. Keep unknown parameters explicitly unknown. Classify every
output OBSERVED, INFERRED, SIMULATED, or UNVERIFIED, and never describe simulated
trajectories as observed migration routes.
