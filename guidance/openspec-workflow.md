# RatSight evidence-driven workflow

This is the authoritative project workflow. `openspec/README.md` covers OpenSpec
CLI mechanics; runtime-specific orchestration stays outside this contract.

## Lifecycle

Research and record evidence → proposal → specifications and design →
adversarial review → resolve blocking findings → tasks → implementation →
independent code review → QA and applicable scientific validation →
traceability → quality gate → human acceptance when required → archive.

Adversarial review happens before tasks. Code review happens after
implementation and must inspect the actual diff and relevant surrounding code.

## Responsibilities

| Layer | What it checks or decides | What it cannot prove |
| --- | --- | --- |
| OpenSpec CLI | Schema validity, artifact dependencies, change validity, status, and delta requirement names | That a review or scientific judgment is sound |
| Quality Gate | Recorded state in `verification/gate.json`, required review reports, exact requirement coverage, and OpenSpec CLI results | That reviews happened, contexts were independent, commands ran, approval was human, or science is valid |
| CI | Repository lint, type, test, and frontend checks listed below | Human approval or gate state for every active change |
| Agents and reviewers | Perform adversarial review, code review, QA, scientific assessment, and honest evidence recording | Human-controlled approval |
| Human | Decide required approval and non-blocking risk exceptions | Machine authentication by the gate |

The schema enforces artifact presence and ordering: adversarial review requires
specifications and design; tasks require those artifacts and adversarial review;
apply requires tasks. OpenSpec validates the schema and spec/change formats.
The project gate does not parse Markdown headings or tables.

## Gate contract

Run `make openspec-gate CHANGE=<change>` or
`uv run python scripts/openspec_quality_gate.py <change>`.
The gate requires non-empty `adversarial-review.md`,
`verification/code-review.md`, and `verification/gate.json`.

The gate checks that:

- Both reviews record different reviewer/author or reviewer/implementer
  identities, a separate-context method, a valid decision, and consistent
  finding state. `NONE` cannot satisfy mandatory review. Recorded identity and
  method are provenance, not proof; include runtime context evidence when
  available, and state limits honestly.
- Every unresolved `BLOCKING` finding fails, regardless of approval. Blocking
  findings cannot be waived. A non-blocking `ACCEPTED_RISK` must preserve its
  residual risk and be named exactly in a required human approval.
- Engineering traceability uses exact `<spec-name>#<requirement-name>` IDs
  returned by OpenSpec. Each changed requirement has a mapping; verified rows
  point to existing implementation and test files and recorded verification
  IDs.
- Verification entries record command, result, reference, and exit code `0`.
  This is a recorded claim, not proof that the command ran. Prefer actual CI or
  test artifacts as references when available.
- Science applicability is explicit. Applicable claims name an exact evidence
  ID, source file under `docs/evidence/`, assumption, parameter, model, data
  class, status, and validation-run IDs. The exact `- Evidence ID: <id>` line
  must occur in the cited file; this avoids substring matches, not scientific
  judgment. Pure engineering changes use `applicable: false` with a reason.
- Required approval has a recorded trigger, `APPROVED` decision, approver,
  reference, scope, and `verification/acceptance.md`. Acceptance file is not
  required when approval is not required.

`gate.json` is canonical machine state. Review Markdown is narrative; the gate
checks its presence only and does not cross-check its contents against JSON.
Optional `verification/traceability.md` is also narrative. Recorded values can
be false or incomplete while passing, and scientific correctness is not
machine-verifiable here.

### Human approval triggers

Project policy requires a human decision for material architecture changes,
new scientific assumptions, unknown-parameter defaults, sensitive-data policy,
security or policy changes, and non-blocking accepted-risk exceptions. Record
`approval.required: true` and the applicable trigger in `gate.json`. The gate
cannot detect whether a trigger applies or authenticate the approver; reviewers
must not omit a required decision to obtain a pass. Agent consensus is not
approval.

### Scientific integrity

Preserve source, license, location, method, applicability, processing, CRS,
assumptions, model/version/seed, and uncertainty where applicable. Keep
`OBSERVED`, `INFERRED`, `SIMULATED`, and `UNVERIFIED` distinct. Unknown data are
not zero; simulated output is not an observed route or event. The gate checks
recorded classification and references only. Scientific validity belongs to
scientific review and evidence-based validation.

## Runtime, CI, and archive boundaries

The gate is a Python CLI and OpenSpec CLI wrapper; it has no dependency on an
agent runtime or orchestration system. `--skip-openspec` skips native schema,
change, status, and requirement-coverage checks and reports that limitation.
It is not equivalent to a full pass.

CI installs OpenSpec 1.14.1 and runs Ruff, basedpyright, Python tests for
`scripts/tests`, API, geo, and simulation packages, plus frontend lint,
typecheck, tests, and build. `scripts/tests` includes an integration test of
the installed OpenSpec CLI and custom schema. CI does not run the quality gate
against every active change and does not authenticate review or approval
records.

`make openspec-archive CHANGE=<change>` runs the gate and then native archive.
It is a project wrapper, not an interception hook: direct `openspec archive`
bypasses the gate. Exit codes are `0` pass, `1` blocked, `2` usage error.
A pass validates recorded state and CLI results only; it is not proof of review,
command execution, human approval, or scientific validity.

```sh
openspec schema validate evidence-driven
openspec validate <change>
make openspec-gate CHANGE=<change>
make openspec-archive CHANGE=<change>
uv run pytest scripts/tests
```
