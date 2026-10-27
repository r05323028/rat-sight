# RatSight OpenSpec

The repository selects the project-local `evidence-driven` schema in
`openspec/config.yaml`. Project review, evidence, and approval policy lives in
`guidance/openspec-workflow.md`.

## Native OpenSpec

The schema adds an adversarial-review planning artifact and task dependency:

```text
proposal -> specs + design -> adversarial-review -> tasks -> apply
```

OpenSpec CLI validates schema syntax, artifact dependencies, change/spec
requirements, status, and delta output. It enforces artifact presence and
ordering only; it does not verify review quality or post-implementation work.

```sh
openspec schema validate evidence-driven
openspec validate <change>
openspec status --change <change> --json
openspec show <change> --json --deltas-only
openspec instructions tasks --change <change>
```

Use `.openspec.yaml` `skip_specs: true` only for changes with no
requirement-level behavior change.

## Project quality gate

`make openspec-gate CHANGE=<change>` runs
`uv run python scripts/openspec_quality_gate.py <change>`. It delegates schema,
change, status, and requirement lookup to the installed OpenSpec CLI, then
checks recorded state in `verification/gate.json` and presence of required
narrative reports. The gate does not parse report formatting or authenticate
review, execution, approval, or scientific claims. See the workflow guide for
checks and limitations.

`make change-review CHANGE=<change>` and `make change-status CHANGE=<change>`
show the current review packet without modifying it. The project owner records
an explicit decision with `make change-accept CHANGE=<change>`; decisions live in
`verification/owner-decision.json`, separate from policy approval receipts.
`make openspec-archive CHANGE=<change>` runs the gate and requires a current,
matching `ACCEPTED` owner decision before native archive. Direct `openspec archive`
remains an upstream bypass and does not consult project policy.

```sh
uv run pytest scripts/tests
```

The schema integration tests exercise the installed OpenSpec CLI, including
custom-schema validation and task dependencies. CI also runs repository lint,
type, test, and frontend checks; it does not gate each active change.
