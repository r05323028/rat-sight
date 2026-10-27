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
Owner decisions MUST be stored in `verification/owner-decision.json` separately from `verification/acceptance.md`, preserve history, record the reviewed commit, and bind the decision to a deterministic fingerprint of the complete committed tree by path, mode, and blob, excluding only that file. Any implementation, configuration, or evidence change MUST make the decision stale. Final acceptance MUST use a clean snapshot.

#### Scenario: changed evidence
- **WHEN** implementation, configuration, or verification evidence changes after acceptance
- **THEN** review reports the prior decision as stale and it cannot authorize archival

#### Scenario: decision-only commit
- **WHEN** an otherwise unchanged accepted tree changes only the excluded owner-decision record
- **THEN** the content fingerprint remains current and does not self-invalidate

#### Scenario: dirty working tree
- **WHEN** implementation files are staged, unstaged, or untracked and nonignored at final acceptance
- **THEN** acceptance is refused rather than recording an unidentified snapshot

### Requirement: Archive requires current owner acceptance
`make openspec-archive CHANGE=<change>` MUST run existing validation and quality checks and MUST refuse archival unless all required tasks are complete, verification evidence and the Quality Gate pass, mandatory policy approvals pass, the working tree is clean apart from the decision record, and a current owner decision is `ACCEPTED` for the reviewed implementation-and-evidence snapshot.

#### Scenario: deferred owner decision
- **WHEN** owner decision is missing, deferred, changes-requested, or stale
- **THEN** the wrapper exits without invoking native archive

#### Scenario: incomplete tasks or failed evidence
- **WHEN** required implementation tasks are incomplete or verification/gate/policy approval fails
- **THEN** acceptance and archival are refused even if a Quality Gate artifact exists

### Requirement: Evidence-derived readiness
Agent readiness MUST require a nonempty list of completed required tasks, verification evidence, a passing Quality Gate, and required policy approvals. Missing, empty, or unchecked task lists MUST NOT be treated as complete implementation. Sections explicitly marked non-goals, future follow-ups, out of scope, or not required are excluded from required-task counting.

#### Scenario: recorded gate with unfinished tasks
- **WHEN** a gate artifact passes but required implementation tasks remain unchecked
- **THEN** readiness and acceptance remain blocked

### Requirement: Durable workflow boundary
Guidance MUST distinguish mandatory human policy approval, agent readiness, and final owner acceptance; agents MUST stop at `READY_FOR_HUMAN_REVIEW`, and later Lead executions MUST be able to discover durable owner feedback without the original Pi session.

#### Scenario: requested revisions
- **WHEN** a future Lead execution starts after `CHANGES_REQUESTED`
- **THEN** it can read the decision record and resume verification and implementation without recovering the original runtime session
