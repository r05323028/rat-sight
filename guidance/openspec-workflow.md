# RatSight evidence-driven workflow

This is the authoritative project workflow. `openspec/README.md` covers OpenSpec
CLI mechanics; runtime-specific orchestration stays outside this contract.

## Choosing a workflow

- Trivial local changes: implement directly, run relevant checks, and review.
- Feature or public-contract changes: use the lifecycle below.
- Scientific or model-related changes: use the lifecycle with evidence, assumptions,
  and validation appropriate to claims.

Use judgment; do not add a risk score or workflow state.

## Lifecycle

Research and record evidence → proposal → specifications and design →
adversarial review → resolve blocking findings → tasks → preflight → implementation →
code review → QA and applicable scientific validation → traceability → quality gate
→ Ready for Human Review → local project-owner acceptance → explicit archive
(policy-required human approval is a separate trigger within this flow).

Adversarial review happens before tasks. Code review happens after
implementation and must inspect the actual diff and relevant surrounding code.

Preflight must pass before the first implementation edit. It checks recorded
review state only, so passing it is not evidence that the review was good.

## What reviews must cover

Reviews are judgments, not inventories. Both reviews work from the repository,
not only from the change directory.

- **Changed behavior.** State the observable before and after for each behavior
  the change alters. A renamed file or function is not a behavior change.
- **Callers, consumers, and shared contracts.** Read who calls the changed code and
  what they assume. Cover signatures, request/response shapes, database columns,
  configuration keys, CRS and units, encodings, ordering, and nullability.
- **Implicit invariants.** Name the properties the code relies on without restating
  them (idempotency, authorization, transaction boundaries, cache keys, provenance)
  and say whether each still holds.
- **Impact, predicted versus actual.** The design predicts a blast radius; the code
  review compares it with the diff. Anything that appeared or disappeared gets a line.
- **Untested paths.** Name the negative and boundary cases no test exercises. Do not
  imply coverage that does not exist.
- **Existing specifications and history.** Check `openspec/specs/` for capabilities
  that already constrain the behavior, and `docs/decisions/` and `docs/evidence/` for
  binding assumptions. Cite paths; do not copy repository knowledge into new artifacts.

Keep findings concise and supported by evidence someone else could check. A finding
records `severity`, `verification` (`VERIFIED`, `SUSPECTED`, `UNVERIFIED`, `JUDGMENT`),
and `status`; `BLOCKING` findings also record `evidence`.

## Behavioral traceability

File existence is not verification. For each applicable requirement record the
expected observable behavior, the implementation symbol, the test that drives it and
the assertion that would fail if it regressed, the missing negative and boundary
scenarios, and whether coverage is verified or inferred. Inferred coverage is
`PARTIALLY_VERIFIED` with a `gap`, and under record version 3 it blocks readiness.
A test name, scenario comment, or path is a pointer; it is not proof. See
`openspec/schemas/evidence-driven/templates/verification/traceability.md`.

## Responsibilities

| Layer | What it checks or decides | What it cannot prove |
| --- | --- | --- |
| OpenSpec CLI | Schema validity, artifact dependencies, change validity, status, and delta requirement names | That a review or scientific judgment is sound |
| Quality Gate | Recorded state in `verification/gate.json`, required review reports, exact requirement coverage, and OpenSpec CLI results | That review reports reflect substantive work, commands ran, approval was human, or science is valid |
| CI | Repository lint, type, test, and frontend checks listed below | Human approval or gate state for every active change |
| Agents and reviewers | Perform adversarial review, code review, QA, scientific assessment, and honest evidence recording; read callers, contracts, and existing specifications rather than only the diff | Human-controlled approval, review independence, and semantic correctness |
| Human | Decide required approval and non-blocking risk exceptions | Machine authentication by the gate |

The schema enforces artifact presence and ordering: adversarial review requires
specifications and design; tasks require those artifacts and adversarial review;
apply requires tasks. OpenSpec validates the schema and spec/change formats.
The project gate does not parse Markdown headings or tables.

## Gate contract

Run `make openspec-preflight CHANGE=<change>` before the first implementation edit and
`make openspec-gate CHANGE=<change>` before review or archive.
The readiness gate requires non-empty `adversarial-review.md`,
`verification/code-review.md`, and `verification/gate.json`.

`--stage planning` checks only the pre-implementation contract: planning artifacts,
a non-empty adversarial review, a recorded decision that is not `BLOCKED`, no
unresolved `BLOCKING` finding, and recorded evidence for every `BLOCKING` finding.
It does not check tasks, verification, traceability, science, or approval.

`verification/gate.json` must declare `"schema_version"`: `3` for current records, `2`
only for records that predate the versioned contract. A record without the field is
rejected, so strictness cannot be lost by omitting it. Version 2 is accepted only
for the frozen list of legacy change names; any other change that declares it is
rejected. A legacy record keeps its tolerance and reports it as a warning, and it
should declare version 3 the next time the change is edited.

`--skip-openspec` is permitted only for the planning stage, where it records a
warning. At readiness the gate treats it as an error: requirement coverage from
the OpenSpec CLI is part of the contract, and skipping it is not a full pass.

The gate checks that:

- Both reviews need valid decisions and finding states. `BLOCKED` decisions
  fail; `PASS` with unresolved findings fails; unresolved `BLOCKING` findings
  always fail. A non-blocking `ACCEPTED_RISK` must preserve residual risk and
  have human approval tied to that exact finding ID.
- Each finding records `severity`, `verification` (`VERIFIED`, `SUSPECTED`,
  `UNVERIFIED`, `JUDGMENT`), and `status`. Under version 3 the verification axis is
  required and `BLOCKING` findings need `evidence`. Evidence is a claim: the gate
  cannot check that it is true, only that it was written down.
- Engineering traceability uses exact `<spec-name>#<requirement-name>` IDs
  returned by OpenSpec. Each changed requirement has a mapping; verified rows
  point to existing implementation and test files and recorded verification
  IDs. Under version 3, `NOT_APPLICABLE` is accepted only for requirements the
  change removes, and `PARTIALLY_VERIFIED` blocks readiness instead of only
  warning.
- Verification entries record command, result, reference, and exit code `0`.
  This is a recorded claim, not proof that the command ran. Under version 3 every
  reference resolves to a file in this repository (relative to the repository root
  or the change directory) or is an explicit `ci:`/`https:` reference; absolute
  paths, missing files, and the gate record itself are rejected. Resolution proves
  the artifact exists, not that the command ran. Prefer actual CI or test output;
  when a claim has no machine artifact, an agent-authored report may carry it, but
  the entry must say so. A report that only restates the claim is a pointer.
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
the installed OpenSpec CLI and custom schema. Changed-only validation resolves
its base from the pull-request base or the pre-push commit and checks out full
history; when the base cannot be resolved it fails instead of validating
nothing. CI does not run the quality gate against every active change and does
not authenticate review or approval records.

Use `make change-review CHANGE=<change>` for a read-only packet and
`make change-status CHANGE=<change> --` (or the script's `status --json`) for
machine-readable state. The project owner uses `make change-accept
CHANGE=<change>` in a local interactive terminal; the CLI records decisions in
`verification/owner-decision.json`. TTY confirmation is a practical safeguard,
not authentication. Agents must never write owner decisions.

`make openspec-archive CHANGE=<change>` runs the gate, requires current
`ACCEPTED` owner state matching its evidence fingerprint, then invokes native
archive. Missing, deferred, changes-requested, stale, or gate-invalid states
block. Uncommitted state is recorded explicitly; the evidence fingerprint is
still required to match. Direct `openspec archive` bypasses this project wrapper and that
limitation is documented. A pass validates recorded state and CLI results only;
it is not proof of review, command execution, human identity, or scientific
validity.

When a fresh Lead execution starts, read `verification/owner-decision.json`.
`CHANGES_REQUESTED` feedback is durable implementation input; resume the active
change, refresh evidence, and return to Ready for Human Review. Do not wait for
or depend on the original Pi session.

```sh
openspec schema validate evidence-driven
openspec validate <change>
make openspec-gate CHANGE=<change>
make change-review CHANGE=<change>
make change-status CHANGE=<change>
make change-accept CHANGE=<change>
make openspec-archive CHANGE=<change>
uv run pytest scripts/tests
```
