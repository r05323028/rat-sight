## ADDED Requirements

### Requirement: Frozen legacy record version

The quality gate SHALL accept `schema_version: 2` only for the frozen set of change records that
predate version 3. Any other change declaring version 2 SHALL be rejected with
`GATE-RECORD-VERSION-LEGACY` and SHALL still be evaluated under the current checks. A frozen
legacy change MAY declare version 3 to opt into the current checks.

#### Scenario: A new change cannot downgrade its record

- **WHEN** a change outside the frozen set declares `schema_version: 2` with a partially verified requirement
- **THEN** the gate reports `GATE-RECORD-VERSION-LEGACY` as an error
- **AND** the current traceability checks still run and report the gap

#### Scenario: A frozen legacy record still passes planning

- **WHEN** a frozen legacy change declares `schema_version: 2`
- **THEN** the gate warns with `GATE-RECORD-LEGACY` and evaluates it under the legacy rules
- **AND** it reports no `GATE-RECORD-VERSION-LEGACY` error

### Requirement: Non-vacuous changed-only CI validation

The CI validator SHALL resolve its diff base from the triggering event: the pull-request base from
`GITHUB_BASE_REF` as `origin/<base>`, a push `before` commit, or the default branch. It SHALL
fail when no base resolves, when the base resolves to HEAD, or when the diff fails. It SHALL report
a resolved range with no OpenSpec change paths as a zero-change result that names what ran.

#### Scenario: Shallow checkout is rejected

- **WHEN** the validator runs in a shallow clone whose base ref resolves to HEAD
- **THEN** it exits non-zero and states that the range base resolves to HEAD
- **AND** it does not report a successful validation of zero changes

#### Scenario: Pull request with unrelated changes

- **WHEN** a pull request against `main` touches no OpenSpec change paths
- **THEN** the validator exits 0 with `evaluated: 0` and a note that only schema validation ran
- **AND** it does not claim that any change was validated

### Requirement: Consistent task marker counting

The quality gate and the owner-acceptance CLI SHALL share one task parser. The parser SHALL count
every checkbox marker, SHALL treat only `[x]` and `[X]` as complete, and SHALL warn about other
non-empty markers while keeping them unfinished.

#### Scenario: Non-standard marker stays unfinished

- **WHEN** a required task is written as `- [~] 1.2 Skipped`
- **THEN** it counts as an unfinished required task and the change is not complete
- **AND** the gate reports `GATE-TASKS-MARKER`

#### Scenario: Bracketed prose is not a task

- **WHEN** a line reads `- [API] Document the endpoint`
- **THEN** the parser does not count it as a task

### Requirement: Evidence references are pointers

The gate SHALL require each verification reference to resolve, and the templates and guidance SHALL
present a resolvable reference as a pointer to evidence rather than proof of correctness. The gate
template SHALL NOT default to agent-authored verification prose.

#### Scenario: Template asks for a reproducible artifact

- **WHEN** a change starts from the gate template
- **THEN** the verification reference is a placeholder for a CI run or artifact
- **AND** the guidance states that a passing reference does not establish correctness

### Requirement: Skip-openSpec is planning-only

`--skip-openspec` SHALL remain available at planning stage and SHALL be an error at readiness.

#### Scenario: Readiness cannot skip requirement coverage

- **WHEN** the gate runs at readiness with `--skip-openspec`
- **THEN** it reports `GATE-OPENSPEC-SKIPPED` as an error and exits non-zero
- **AND** the message points to `--stage planning`

### Requirement: Upstream schema instructions are preserved

The project schema SHALL keep the upstream apply instruction verbatim and append project-specific
requirements after it instead of replacing upstream text.

#### Scenario: Upstream apply instruction survives

- **WHEN** the evidence-driven schema is compared with the installed spec-driven schema
- **THEN** the upstream apply instruction appears unchanged
- **AND** the project addendum follows it

### Requirement: Illustrative benchmark labelling

The review-workflow benchmark SHALL state its classification, ground truth, and missing artifacts,
and SHALL NOT report a precision value that was never computed.

#### Scenario: Benchmark without preserved transcripts

- **WHEN** a reader inspects `docs/benchmarks/openspec-review-workflow.json`
- **THEN** the record is classified as illustrative and lists prompts and transcripts as not preserved
- **AND** its precision field is null with an explanation
