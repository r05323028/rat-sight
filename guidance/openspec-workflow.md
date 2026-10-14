# OpenSpec evidence-driven workflow (authoritative)

This is the single authoritative description of the RatSight change lifecycle.
Role guidance points here instead of restating it: Lead decisions are in
`guidance/lead.md`, human escalation in `guidance/human-escalation.md`, and the
OpenSpec mechanics in `openspec/README.md`.

## Lifecycle

```text
Research -> Evidence Collection -> Proposal -> Specifications -> Design
  -> Adversarial Review -> Findings Resolution -> Tasks -> Implementation
  -> Independent Code Review -> QA / Scientific Model Validation
  -> Traceability Validation -> Final Verification
  -> Human Acceptance (when required) -> Archive
```

## Who enforces what

| Layer | Mechanism | Covers |
| --- | --- | --- |
| Schema (`openspec/schemas/evidence-driven/schema.yaml`) | artifact `requires` edges | artifact presence and ordering: `adversarial-review` after `specs`+`design`, `tasks` after `adversarial-review`, `apply` after `tasks` |
| Script (`scripts/openspec_quality_gate.py`, `make openspec-gate`) | deterministic checks over the change directory plus OpenSpec CLI validation | review-record completeness and independence fields, findings resolved, PASS/PASS_WITH_WARNINGS/BLOCKED decisions, requirement-to-evidence traceability, scientific classification and provenance, acceptance approval records |
| Agent guidance (this file) | role duties | actually running the reviews, judging evidence quality, writing honest records |
| Human | recorded approval | acceptance decisions the project marks as human-controlled |
| Runtime integration (outside this document) | the runtime's own guidance | assigning work, providing separate execution contexts, managing sessions, delivering human decisions |

The schema is presence and ordering only: it never proves a review happened, and
the CLI has no post-implementation hook. The gate reads evidence, so a checked
box, an existing file, or an agent's success claim never passes it.

## Runtime independence

This workflow is a project contract, not a runtime feature. It applies unchanged
in a standalone coding agent (Pi, Codex, Claude Code, or any compatible agent),
in a human-driven terminal session, or under an orchestrated fleet. Nothing in
this document requires a particular orchestration framework, agent identity,
session API, or messaging protocol, and no stage may be skipped because a
runtime cannot provide a mechanism.

- Roles are logical responsibilities: Author, Implementer, Reviewer, Validator,
  Approver. Map them onto whatever the runtime offers, including one person or
  one agent holding several of them.
- Independence is an observable property, not a product feature: a different
  identity from the author or implementer, access to the actual artifacts and
  specifications, recorded findings, and recorded resolutions. The runtime
  chooses how to provide that context.
- Runtime metadata (session ids, worktree paths, model names, ticket or queue
  references) is optional provenance. Record it when it helps someone verify a
  claim; never require it for a record to be valid.
- When no independent context is available, do not fabricate one: record the
  limitation, keep the review classified as self-review, and obtain an explicit
  human waiver in the review record. The gate fails a record that declares NONE
  without a waiver reference.
- Human approval uses whatever channel the environment provides. Record the
  decision reference, not the transport; role guidance names the route for a
  given runtime.

## Stages

1. **Research and evidence.** Researcher records verifiable sources in `docs/evidence/` with evidence IDs plus location, species, method, applicability, limitations, and confidence. Unknowns stay unknown.
2. **Proposal and specifications.** `openspec new change <name>`; state motivation, boundaries, data classes, assumptions, and evidence links. Requirements define observable behavior, not scientific conclusions.
3. **Design.** Separate observed, inferred, simulated, and unverified data paths. For model work state parameters, units, provenance, assumptions, reproducibility, uncertainty, and the validation plan.
4. **Adversarial review (planning gate).** Write `adversarial-review.md` from its template in a reviewer context that did not author the proposal, specs, or design, and record reviewer context, author context, and the independence mechanism (SEPARATE_SESSION, SEPARATE_WORKTREE, SEPARATE_AGENT, SEPARATE_MODEL, or HUMAN; NONE needs a recorded exception reason and a human waiver reference, and can only pass with a warning). Challenge review scope, assumptions, requirement gaps, design counterexamples, scientific validity, and unverifiable acceptance criteria. The decision is PASS, PASS_WITH_WARNINGS, or BLOCKED. BLOCKING findings must be resolved in proposal/specs/design before `tasks.md` exists: the schema will not offer tasks until the artifact exists, and the gate rejects unresolved blockers, self-review, and empty sections.
5. **Findings resolution and tasks.** Write `tasks.md` only after step 4. Do not encode work that contradicts the recorded decision; a finding left OPEN or DEFERRED stays a tracked task. Include the post-implementation stages below as tasks.
6. **Implementation.** Execute tasks, mark checkboxes as work lands, and land tests and docs inside the group whose work needs them.
7. **Independent code review.** `verification/code-review.md` from its template, written in a reviewer context separate from the implementer, inspecting the actual diff and the connected code rather than the implementer's summary. Record both contexts, the independence mechanism, and how independence can be verified (session id, worktree path, agent or model identity). Independence is achieved by running the review in that separate context; it is verified from the recorded identifier, which is why the gate requires the "Verification of independence" field, rejects a reviewer that is the implementer, requires an exception reason and a resolvable human waiver reference when the mechanism is NONE, and warns rather than silently accepting weak independence. The decision is PASS, PASS_WITH_WARNINGS, or BLOCKED.
8. **QA and scientific model validation.** Run the tests and record exact commands and results; for model changes record validation limits. Never invent accuracy metrics, and never present SIMULATED output as OBSERVED.
9. **Traceability validation.** `verification/traceability.md`: the engineering chain (requirement -> acceptance criteria -> implementation -> tests -> execution evidence) and, when the change touches science, the scientific chain (research evidence -> assumption -> parameter -> model -> validation evidence). Rows are VERIFIED, PARTIALLY_VERIFIED, UNVERIFIED, or NOT_APPLICABLE with a reason. Purely engineering changes record scientific traceability as NOT_APPLICABLE with a reason instead of inventing claims.
10. **Final verification.** `make openspec-gate CHANGE=<change>`; the gate also runs the OpenSpec CLI. A non-zero exit blocks archive. The gate is standard library only, needs no agent runtime, and runs under `uv run python` (Python 3.10+); under an older interpreter it exits 2 with an actionable message.
11. **Human acceptance.** `verification/acceptance.md` when project policy requires it (architecture change, new scientific assumption, unknown-parameter default, sensitive data policy, acceptance exception). Only a recorded human decision counts; agent consensus is not approval.
12. **Archive.** `make openspec-archive CHANGE=<change>` - the gate must pass first.

## Commands

```sh
openspec schema validate evidence-driven
openspec validate <change>
make openspec-gate CHANGE=<change>
make openspec-archive CHANGE=<change>
uv run pytest scripts/tests          # gate and schema regression tests
```

## Interpreting gate failures

The report lists `GATE-<AREA>-<REASON>` codes: `ARTIFACT`/`SECTION` (missing or empty planning artifacts), `AR` (adversarial review), `CR` (code review), `TR`/`SC` (traceability and scientific claims), `AC` (human acceptance), `FINDING`, `TASKS`/`SPECS`, `SCHEMA`, `OPENSPEC`. Exit `1` means the change is not archivable: resolve the finding in the artifacts or the verification records. Never weaken a check or edit a report to pass. Warnings do not block but must be acknowledged in the record. Weak independence is reported as `GATE-AR-INDEPENDENCE-WEAK` or `GATE-CR-INDEPENDENCE-WEAK`; a `NONE` mechanism with no waiver fails as `GATE-AR-INDEPENDENCE-WAIVER` or `GATE-CR-INDEPENDENCE-WAIVER`, and an unresolvable waiver reference fails as `GATE-AR-WAIVER-REFERENCE` or `GATE-CR-WAIVER-REFERENCE`. `--skip-openspec` is a documented limitation, not a pass.

## Human approval is mandatory when

- the change alters architecture boundaries, a scientific assumption, or a default for an unknown parameter;
- evidence is insufficient to justify a claim, or the decision changes policy or scope;
- an adversarial or code-review finding is closed as ACCEPTED_RISK.

Use the human-approval channel the environment provides and record the decision reference in `verification/acceptance.md`. Any reference form works: a decision record path or an external id in any `<scheme>:<id>` form.

## Archive is allowed when

the quality gate exits `0` for the change, every blocking finding is resolved, traceability is recorded (or explicitly NOT_APPLICABLE with a reason), and any required human approval is recorded. Nothing else counts as completion.
