# RatSight OpenSpec

The repository selects the project-local `evidence-driven` schema in
`openspec/config.yaml`. Project review, evidence, and approval policy lives in
`guidance/openspec-workflow.md`.

## Native OpenSpec

The schema adds an adversarial-review planning artifact and task dependency:

```text
proposal -> specs + design -> adversarial-review -> tasks -> apply
```

The `proposal`, `specs`, `design`, and `tasks` instructions embed the OpenSpec
1.14.1 `spec-driven` guidance verbatim and append project-specific addenda. CI
pins that version; when the pin changes, re-compare `schema.yaml` and run
`uv run pytest scripts/tests -k schema`.

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
requirement-level behavior change. The file must also declare the schema:

```yaml
schema: evidence-driven
skip_specs: true
```

## Project quality gate

The gate runs in two stages:

| Stage | Command | Checks |
| --- | --- | --- |
| planning | `make openspec-preflight CHANGE=<change>` | artifacts, adversarial review state, blocking findings, finding evidence |
| readiness | `make openspec-gate CHANGE=<change>` | the planning checks plus tasks, verification, traceability, science, and approval |

`make openspec-validate` (and CI) runs `scripts/openspec_validate_changed.py`,
which only validates schema and `openspec validate` for touched changes. It does
not run tests or the gate. The script resolves the range base explicitly: the
pull-request base on pull requests, the pre-push commit on pushes, or
`--base <ref>` locally. A missing base, a shallow checkout where the base
resolves to HEAD, or a failed diff is an error, so an empty range is never
reported as a successful validation. CI checks out full history (`fetch-depth: 0`)
for that reason.

`--skip-openspec` is a planning-stage aid. At readiness the gate rejects it:
requirement coverage is mandatory before review or archive, so a skipped CLI
cannot be reported as a full pass.

`verification/gate.json` must declare `"schema_version"`: `3` for current records,
`2` only for records that predate the versioned contract. Version 2 is frozen to
the named historical changes; any other change that declares it is rejected, so
declaring an older version cannot weaken the current checks. A legacy change that
is edited again should declare `3` and satisfy the version 3 rules. A record
without the field is rejected rather than silently treated as legacy. Version 3
requires:

- Findings carry three independent axes: `severity`, `verification`
  (`VERIFIED`, `SUSPECTED`, `UNVERIFIED`, `JUDGMENT`), and `status`.
  `BLOCKING` findings must record `evidence`.
- `NOT_APPLICABLE` traceability is allowed only for requirements the change
  removes; added or modified requirements must be verified.
- `PARTIALLY_VERIFIED` blocks readiness; incomplete verification is not success.
- Every verification `reference` resolves to a repository file (relative to the
  repository root or the change directory) or is an explicit `ci:`/`https:`
  reference.

A resolved reference proves an artifact exists. The gate cannot authenticate
review, execution, approval, or scientific claims; it only checks recorded state.

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
