# Human-owned local acceptance

## ADDED Requirements

### Requirement: Read-only change review
The repository MUST provide local `make change-review CHANGE=<change>` and `make change-status CHANGE=<change>` commands that summarize actual OpenSpec artifacts, verification state, policy approval state, Git identity, owner decision state, readiness, and limitations without modifying the change.

#### Scenario: incomplete change
- **WHEN** review runs for an incomplete or unverified change
- **THEN** it reports missing or blocking evidence and does not present the change as accepted

### Requirement: Interactive owner decision
The repository MUST provide `make change-accept CHANGE=<change>` as an interactive terminal workflow with explicit Accept, Request Changes, Defer, and Cancel choices; acceptance MUST require a second exact confirmation and MUST reject non-interactive input.

#### Scenario: cancel
- **WHEN** the owner cancels or confirmation does not match
- **THEN** no owner acceptance decision is written

#### Scenario: request changes
- **WHEN** the owner enters requested changes
- **THEN** the feedback is durably recorded against the change and the change remains active

### Requirement: Revision-bound decision record
Owner decisions MUST be stored in `verification/owner-decision.json` separately from `verification/acceptance.md`, preserve decision history, identify the reviewed Git state and deterministic evidence fingerprint, and report an accepted decision as stale when relevant change evidence changes.

#### Scenario: changed evidence
- **WHEN** implementation or verification evidence changes after acceptance
- **THEN** review reports the prior decision as stale and it cannot authorize archival

### Requirement: Archive requires current owner acceptance
`make openspec-archive CHANGE=<change>` MUST run existing validation and quality checks and MUST refuse archival unless mandatory policy approvals pass and a current owner decision is `ACCEPTED` for the reviewed evidence.

#### Scenario: deferred owner decision
- **WHEN** owner decision is missing, deferred, changes-requested, or stale
- **THEN** the wrapper exits without invoking native archive

### Requirement: Durable workflow boundary
Guidance MUST distinguish mandatory human policy approval, agent readiness, and final owner acceptance; agents MUST stop at `READY_FOR_HUMAN_REVIEW`, and later Lead executions MUST be able to discover durable owner feedback without the original Pi session.

#### Scenario: requested revisions
- **WHEN** a future Lead execution starts after `CHANGES_REQUESTED`
- **THEN** it can read the decision record and resume verification and implementation without recovering the original runtime session
