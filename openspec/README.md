# RatSight OpenSpec

The project-local `evidence-driven` schema is a copy of the installed OpenSpec `spec-driven` schema, forked with the installed CLI. It keeps supported artifacts and required fields unchanged. Validate it with:

```sh
openspec schema validate evidence-driven
```

The schema models proposal → specs → design → tasks and task tracking. It does **not** enforce research evidence, adversarial review, independent code review, scientific validation, traceability, or human acceptance. Those checkpoints are project policy in `guidance/openspec-workflow.md`; do not claim the schema enforces them.

For a change, use the installed CLI (`openspec new change <name>`, `openspec validate <name>`, `openspec archive <name>`). Use its proposal/spec/design/tasks templates as written. Implementation begins only after proposal/spec/design review; record completion and verification in tasks. Archive only after review, QA, validation, traceability, and acceptance checkpoints pass.

Evidence belongs in `docs/evidence/`; cite stable evidence IDs and parameter IDs in specs/designs. Keep unknown parameters explicitly unknown. Classify outputs OBSERVED, INFERRED, SIMULATED, or UNVERIFIED. Never describe simulated trajectories as observed migration routes.
