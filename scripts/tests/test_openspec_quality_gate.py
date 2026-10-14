"""Tests for the RatSight OpenSpec evidence quality gate.

The gate is the project's archive-time acceptance check: it reads a change's
planning artifacts plus the verification records under `verification/`, and
blocks the archive when the recorded evidence is missing, inconsistent, or
claims a result the records do not support.

Every test builds a throwaway repository under pytest's tmp_path, so the real
openspec/ tree is never touched, and runs the gate as a subprocess: the exit
code and the JSON report are the contract. The OpenSpec CLI itself is skipped
with --skip-openspec (the CLI path runs in CI and in `make openspec-gate`).
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
GATE = REPO_ROOT / "scripts" / "openspec_quality_gate.py"
SCHEMA = REPO_ROOT / "openspec" / "schemas" / "evidence-driven" / "schema.yaml"
CHANGE = "gate-fixture"

BT = chr(96)
TEST_COMMAND = BT + "pytest services/api/tests/test_fixture.py" + BT
FIXTURE_SOURCE = "services/api/src/fixture.py"
FIXTURE_TEST = "services/api/tests/test_fixture.py"
EVIDENCE_RECORD = "docs/evidence/model-validation.md"
ACCEPTANCE_RECORD = "docs/decisions/acceptance-fixture.md"
REQUIREMENT_ID = "gate-fixture#fixture-capability-returns-a-constant"
SCENARIO_ID = REQUIREMENT_ID + "/constant-is-returned"
REVIEWED_AT = "2026-10-14"
NOT_APPLICABLE_REASON = "engineering-only fixture, no model or data claim"


def row(*cells: str) -> str:
    """One Markdown table row."""
    return "| " + " | ".join(cells) + " |"


def table(header: str, rows: tuple) -> str:
    """A Markdown table: header row, divider, then the given rows."""
    columns = header.count("|") - 1
    return "\n".join((header, row(*(["---"] * columns)), *rows))


AR_HEADER = row(
    "Finding ID",
    "Severity",
    "Affected Artifact",
    "Description",
    "Evidence or Reasoning",
    "Proposed Resolution",
    "Resolution Status",
)
CR_HEADER = row(
    "Finding ID",
    "Severity",
    "File and Location",
    "Description",
    "Reproduction or Supporting Evidence",
    "Recommended Correction",
    "Resolution Status",
)
AR_MINOR = row(
    "AR-1",
    "MINOR",
    "design.md",
    "Design omits the return type.",
    "design.md has no type section",
    "State the type in design.md",
    "RESOLVED",
)
AR_BLOCKING_OPEN = row(
    "AR-1",
    "BLOCKING",
    "design.md",
    "Design omits the return type.",
    "design.md has no type section",
    "State the type in design.md",
    "OPEN",
)
CR_MINOR = row(
    "CR-1",
    "MINOR",
    FIXTURE_SOURCE + ":12",
    "Naming is terse.",
    "read of the file",
    "Rename the local variable",
    "RESOLVED",
)
CR_BLOCKING_ACCEPTED = row(
    "CR-1",
    "BLOCKING",
    FIXTURE_SOURCE + ":12",
    "Naming is terse.",
    "read of the file",
    "Rename the local variable",
    "ACCEPTED_RISK",
)
FOLLOW_UP_HEADER = row("Finding ID", "Re-verification command or check", "Result")
FOLLOW_UP_ROW = row("CR-1", "read " + FIXTURE_SOURCE + ":12", "the variable is renamed")
EXECUTION_HEADER = row("Command", "Exit Code", "Result Summary", "Recorded By")
EXECUTION_ROW = row(TEST_COMMAND, "0", "3 passed", "reviewer-d")
ENGINEERING_HEADER = row(
    "Requirement ID",
    "Acceptance Criteria / Scenario",
    "Implementation",
    "Tests",
    "Execution Evidence",
    "Status",
    "Residual Gaps",
)
ENGINEERING_ROW = row(
    REQUIREMENT_ID,
    SCENARIO_ID,
    FIXTURE_SOURCE + ":1-20",
    FIXTURE_TEST + ":1-15",
    TEST_COMMAND,
    "VERIFIED",
    "none",
)
SCIENTIFIC_HEADER = row(
    "Evidence ID",
    "Scientific Assumption",
    "Parameter ID",
    "Mathematical Model",
    "Data Class",
    "Validation Evidence",
    "Status",
    "Residual Gaps",
)
UNPLANNED_HEADER = row("Deviation ID", "Description", "Spec impact", "Reviewed by", "Decision")
NO_INDEPENDENCE_REASON = "no separate reviewer context was available"
EXTERNAL_WAIVER = "issue:42"


def independence_lines(mechanism: str, reason: str, waiver: str) -> str:
    """Extra Review Record lines; only a NONE mechanism needs a reason and waiver."""
    if mechanism != "NONE":
        return ""
    lines = "- Independence exception reason: " + (reason or NO_INDEPENDENCE_REASON) + "\n"
    if waiver:
        lines += "- Independence waiver (human decision reference): " + waiver + "\n"
    return lines


def proposal() -> str:
    return """# Gate fixture proposal

## Why

Exercise the deterministic quality gate.

## What Changes

Add a fixture capability.

## Impact

None outside tests.
"""


def spec(extra_requirement: str = "") -> str:
    body = """# Capability: gate-fixture

## ADDED Requirements

### Requirement: Fixture capability returns a constant

The system SHALL return a constant value.

#### Scenario: Constant is returned

- **WHEN** the fixture capability is called
- **THEN** it returns the constant
"""
    return body + extra_requirement


def design() -> str:
    return """# Design

## Context

Fixture only.

## Decisions

- Keep the fixture trivial.
"""


def tasks(checked: bool = True) -> str:
    mark = "x" if checked else " "
    return (
        "# Tasks\n\n"
        "## 1. Implementation\n\n"
        "- [" + mark + "] 1.1 Add the fixture module (" + FIXTURE_SOURCE + ")\n"
        "- [" + mark + "] 1.2 Add the fixture test (" + FIXTURE_TEST + ")\n"
    )


def adversarial_review(
    *,
    reviewer: str = "reviewer-a (adversarial reviewer)",
    author: str = "author-b (implementer)",
    findings: str = AR_MINOR,
    decision: str = "PASS",
    open_count: str = "0",
    mechanism: str = "SEPARATE_SESSION",
    reason: str = "",
    waiver: str = "",
) -> str:
    return f"""# Adversarial Review

## Review Record

- Change: gate-fixture
- Review type: ADVERSARIAL_REVIEW
- Reviewer (agent/session and role): {reviewer}
- Author context: {author}
- Independence mechanism: {mechanism}
{independence_lines(mechanism, reason, waiver)}
- Artifacts reviewed: proposal.md, design.md, specs/gate-fixture/spec.md
- Reviewed at (UTC): {REVIEWED_AT}

## Review Scope

- Requirements: reviewed
- Architecture: reviewed
- Scientific assumptions: not applicable - engineering-only fixture
- Evidence quality: reviewed
- Acceptance criteria: reviewed
- Failure scenarios: reviewed

## Assumption Challenges

The fixture assumes no concurrency; the spec does not require it.

## Requirement Gaps

None found.

## Design Counterexamples

A caller passing None is unspecified; out of scope for the fixture.

## Scientific Validity

- Evidence applicability: not applicable - no scientific claim
- Biological assumptions: not applicable - no biological model
- Parameter provenance: not applicable - no parameters
- Mathematical assumptions: not applicable - no model
- Model limitations: not applicable - no model
- Falsifiability: not applicable - no scientific claim
- Uncertainty: not applicable - no measurement

## Acceptance Criteria Weaknesses

The scenario is verifiable by a single unit test.

## Findings

{table(AR_HEADER, (findings,))}

## Review Decision

- Decision: {decision}
- Blocking findings open: {open_count}
- Basis for the decision: the only finding is MINOR and resolved
- Required resolutions before tasks.md: none
"""


def code_review(
    *,
    reviewer: str = "reviewer-c (code reviewer)",
    implementer: str = "author-b (implementer)",
    findings: str = CR_MINOR,
    follow_up: str = FOLLOW_UP_ROW,
    decision: str = "PASS",
    open_count: str = "0",
    mechanism: str = "SEPARATE_SESSION",
    reason: str = "",
    waiver: str = "",
) -> str:
    return f"""# Independent Code Review

## Review Record

- Change: gate-fixture
- Review type: INDEPENDENT_CODE_REVIEW
- Reviewer (agent/session and role): {reviewer}
- Implementer context: {implementer}
- Independence mechanism: {mechanism}
{independence_lines(mechanism, reason, waiver)}
- Verification of independence: reviewer session started after implementation
- Diff reviewed: uncommitted worktree, {FIXTURE_SOURCE}
- Coverage: {FIXTURE_SOURCE}, {FIXTURE_TEST}
- Review method: full diff plus surrounding source
- Reviewed at (UTC): {REVIEWED_AT}
- Scope reviewed: {FIXTURE_SOURCE}

## Review Method

- Actual code changes: reviewed
- Relevant surrounding code: reviewed
- Specifications: reviewed
- Design decisions: reviewed
- Tests: reviewed
- Error handling: reviewed
- Security implications: reviewed
- Regression risks: reviewed

## Findings

{table(CR_HEADER, (findings,))}

## Follow-up Verification

{table(FOLLOW_UP_HEADER, (follow_up,))}

## Review Decision

- Decision: {decision}
- Blocking findings open: {open_count}
- Basis for the decision: the only finding is MINOR and resolved
- Residual risk accepted: none
"""


def traceability(
    *,
    reviewer: str = "reviewer-d (traceability validator)",
    engineering_rows: tuple = (ENGINEERING_ROW,),
    execution_rows: tuple = (EXECUTION_ROW,),
    unplanned: str = "- None.",
    sci_applicability: str = "NOT_APPLICABLE",
    sci_reason: str = NOT_APPLICABLE_REASON,
    sci_rows: tuple = (),
    model_validation: str = "not applicable - no model in this change",
    qa_suites: str = TEST_COMMAND,
    decision: str = "VERIFIED",
    unverified_count: str = "0",
) -> str:
    scientific = table(SCIENTIFIC_HEADER, sci_rows) if sci_rows else "- not applicable"
    return f"""# Traceability Validation

## Traceability Record

- Change: gate-fixture
- Traceability reviewer: {reviewer}
- Independence mechanism: SEPARATE_SESSION
- Verified at (UTC): {REVIEWED_AT}
- Scientific Traceability Applicability: {sci_applicability}
- Non-applicability reason: {sci_reason}

## Engineering Traceability

{table(ENGINEERING_HEADER, engineering_rows)}

## Unplanned or Deviations

{unplanned}

## QA and Model Validation

- QA owner: reviewer-d
- Test suites executed: {qa_suites}
- QA result: PASS
- Scientific model validation: {model_validation}

## Execution Evidence

{table(EXECUTION_HEADER, execution_rows)}

## Scientific Traceability

{scientific}

## Traceability Decision

- Decision: {decision}
- Unverified requirements remaining: {unverified_count}
- Basis for the decision: the single requirement is mapped to an executed test
"""


def acceptance(
    *,
    required: str = "NO",
    trigger: str = "NONE",
    decision: str = "APPROVED",
    consensus: str = "no",
    approver: str = "seanchang (repository maintainer)",
    reference: str = ACCEPTANCE_RECORD,
) -> str:
    return f"""# Human Acceptance

## Acceptance Record

- Change: gate-fixture
- Human Acceptance Required: {required}
- Required per: {trigger}
- Non-applicability reason: no architecture or scientific assumption change
- Approver (human identity and role): {approver}
- Approval reference: {reference}
- Approved at (UTC): {REVIEWED_AT}
- Scope of approval: the new parameter default in this change
- Decision: {decision}
- Agent consensus used as approval: {consensus}
"""


def default_files() -> dict:
    """The baseline change: complete, consistent, and expected to pass."""
    return {
        "proposal.md": proposal(),
        "design.md": design(),
        "adversarial-review.md": adversarial_review(),
        "tasks.md": tasks(),
        "specs/gate-fixture/spec.md": spec(),
        "verification/code-review.md": code_review(),
        "verification/traceability.md": traceability(),
        "verification/acceptance.md": acceptance(),
    }


def build_repo(root: Path, files: dict | None = None, remove: tuple = ()) -> Path:
    """Write a throwaway repository holding one change and the project schema."""
    if root.exists():
        shutil.rmtree(root)
    (root / "openspec" / "schemas" / "evidence-driven").mkdir(parents=True)
    shutil.copy(SCHEMA, root / "openspec" / "schemas" / "evidence-driven" / "schema.yaml")
    change = root / "openspec" / "changes" / CHANGE
    (change / "verification").mkdir(parents=True)
    (root / "docs" / "evidence").mkdir(parents=True)
    (root / "docs" / "decisions").mkdir(parents=True)
    (root / ACCEPTANCE_RECORD).write_text(
        "# Acceptance decision\n\nHuman decision recorded 2026-10-14.\n", encoding="utf-8"
    )
    (root / "services" / "api" / "src").mkdir(parents=True)
    (root / "services" / "api" / "tests").mkdir(parents=True)
    (root / FIXTURE_SOURCE).write_text("VALUE = 1\n", encoding="utf-8")
    (root / FIXTURE_TEST).write_text("def test_value():\n    assert True\n", encoding="utf-8")
    (change / ".openspec.yaml").write_text("schema: evidence-driven\n", encoding="utf-8")
    for relative, content in (files or default_files()).items():
        if relative in remove:
            continue
        target = change / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    return root


def run_gate(root: Path, *extra: str, env: dict | None = None) -> tuple:
    """Run the gate the way CI does and return (exit code, JSON report)."""
    result = subprocess.run(
        [
            sys.executable,
            str(GATE),
            CHANGE,
            "--repo-root",
            str(root),
            "--json",
            "--skip-openspec",
            *extra,
        ],
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    try:
        report = json.loads(result.stdout)
    except ValueError:  # pragma: no cover - only when the gate itself crashes
        raise AssertionError(
            "gate produced no JSON report (exit "
            + str(result.returncode)
            + ")\n"
            + result.stdout
            + result.stderr
        ) from None
    return result.returncode, report


def codes(report: dict) -> list:
    """Every error code in a report, for readable assertions."""
    return [error["code"] for error in report["errors"]]


def warnings(report: dict) -> list:
    """Every warning code in a report."""
    return [warning["code"] for warning in report["warnings"]]


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A complete, passing change in a throwaway repository."""
    return build_repo(tmp_path / "repo")


def test_complete_change_passes(repo: Path) -> None:
    code, report = run_gate(repo)
    assert code == 0, report["errors"]
    assert report["passed"] is True
    assert report["errors"] == []
    statuses = {check["name"]: check["status"] for check in report["checks"]}
    assert statuses["adversarial review"] == "ok"
    assert statuses["independent code review"] == "ok"
    assert statuses["traceability validation"] == "ok"
    assert statuses["schema drift"] == "ok"


def test_report_says_what_the_gate_cannot_prove(repo: Path) -> None:
    _code, report = run_gate(repo)
    assert "does not verify that a review happened" in report["note"]


def test_missing_adversarial_review_blocks(tmp_path: Path) -> None:
    repo = build_repo(tmp_path / "repo", remove=("adversarial-review.md",))
    code, report = run_gate(repo)
    assert code == 1
    assert "GATE-ARTIFACT-MISSING" in codes(report)
    assert "GATE-OPENSPEC-SKIPPED" in [item["code"] for item in report["warnings"]]


def test_missing_code_review_record_blocks(tmp_path: Path) -> None:
    repo = build_repo(tmp_path / "repo", remove=("verification/code-review.md",))
    code, report = run_gate(repo)
    assert code == 1
    assert "GATE-CR-MISSING" in codes(report)


def test_missing_traceability_report_blocks(tmp_path: Path) -> None:
    repo = build_repo(tmp_path / "repo", remove=("verification/traceability.md",))
    code, report = run_gate(repo)
    assert code == 1
    assert "GATE-TR-MISSING" in codes(report)


def test_missing_acceptance_record_blocks(tmp_path: Path) -> None:
    repo = build_repo(tmp_path / "repo", remove=("verification/acceptance.md",))
    code, report = run_gate(repo)
    assert code == 1
    assert "GATE-AC-MISSING" in codes(report)


def test_unchecked_task_blocks(tmp_path: Path) -> None:
    files = default_files()
    files["tasks.md"] = tasks(checked=False)
    code, report = run_gate(build_repo(tmp_path / "repo", files))
    assert code == 1
    assert "GATE-TASKS-OPEN" in codes(report)


def test_fabricated_pass_with_open_blocking_finding_blocks(tmp_path: Path) -> None:
    files = default_files()
    files["adversarial-review.md"] = adversarial_review(findings=AR_BLOCKING_OPEN, open_count="1")
    code, report = run_gate(build_repo(tmp_path / "repo", files))
    assert code == 1
    assert "GATE-AR-FABRICATED-PASS" in codes(report)


def test_blocked_review_decision_blocks(tmp_path: Path) -> None:
    files = default_files()
    files["verification/code-review.md"] = code_review(decision="BLOCKED")
    code, report = run_gate(build_repo(tmp_path / "repo", files))
    assert code == 1
    assert "GATE-CR-BLOCKED" in codes(report)


def test_decision_count_must_match_the_findings_table(tmp_path: Path) -> None:
    files = default_files()
    files["adversarial-review.md"] = adversarial_review(open_count="3")
    code, report = run_gate(build_repo(tmp_path / "repo", files))
    assert code == 1
    assert "GATE-DECISION-COUNT" in codes(report)


def test_invalid_review_decision_value_blocks(tmp_path: Path) -> None:
    files = default_files()
    files["verification/code-review.md"] = code_review(decision="LOOKS_FINE")
    code, report = run_gate(build_repo(tmp_path / "repo", files))
    assert code == 1
    assert "GATE-CR-DECISION" in codes(report)


def test_blocking_finding_closed_without_human_approval_blocks(tmp_path: Path) -> None:
    files = default_files()
    files["verification/code-review.md"] = code_review(findings=CR_BLOCKING_ACCEPTED)
    code, report = run_gate(build_repo(tmp_path / "repo", files))
    assert code == 1
    assert "GATE-CR-WAIVER-APPROVAL" in codes(report)


def test_adversarial_self_review_blocks(tmp_path: Path) -> None:
    files = default_files()
    files["adversarial-review.md"] = adversarial_review(reviewer="author-b (implementer)")
    code, report = run_gate(build_repo(tmp_path / "repo", files))
    assert code == 1
    assert "GATE-AR-SELF-REVIEW" in codes(report)


def test_code_review_by_the_implementer_blocks(tmp_path: Path) -> None:
    files = default_files()
    files["verification/code-review.md"] = code_review(reviewer="author-b (implementer)")
    code, report = run_gate(build_repo(tmp_path / "repo", files))
    assert code == 1
    assert "GATE-CR-SELF-REVIEW" in codes(report)


def test_traceability_reviewer_may_not_be_the_implementer(tmp_path: Path) -> None:
    files = default_files()
    files["verification/traceability.md"] = traceability(reviewer="author-b (implementer)")
    code, report = run_gate(build_repo(tmp_path / "repo", files))
    assert code == 1
    assert "GATE-TR-SELF-VALIDATION" in codes(report)


def test_executed_test_without_a_run_record_blocks(tmp_path: Path) -> None:
    files = default_files()
    files["verification/traceability.md"] = traceability(execution_rows=())
    code, report = run_gate(build_repo(tmp_path / "repo", files))
    assert code == 1
    assert "GATE-TR-QA-SUITES" in codes(report)


def test_unverified_requirement_blocks(tmp_path: Path) -> None:
    files = default_files()
    files["verification/traceability.md"] = traceability(
        engineering_rows=(ENGINEERING_ROW.replace("| VERIFIED |", "| UNVERIFIED |"),)
    )
    code, report = run_gate(build_repo(tmp_path / "repo", files))
    assert code == 1
    assert "GATE-TR-UNVERIFIED" in codes(report)


def test_requirement_without_a_traceability_row_blocks(tmp_path: Path) -> None:
    files = default_files()
    files["specs/gate-fixture/spec.md"] = spec(
        """
### Requirement: Second capability exists

The system SHALL expose a second capability.

#### Scenario: Second capability is callable

- **WHEN** it is called
- **THEN** it responds
"""
    )
    code, report = run_gate(build_repo(tmp_path / "repo", files))
    assert code == 1
    assert "GATE-TR-COVERAGE" in codes(report)


def test_unplanned_deviation_reviewed_by_its_implementer_blocks(tmp_path: Path) -> None:
    files = default_files()
    files["verification/traceability.md"] = traceability(
        unplanned=table(
            UNPLANNED_HEADER,
            (row("D-1", "Extra helper added", "none", "author-b (implementer)", "RESOLVED"),),
        )
    )
    code, report = run_gate(build_repo(tmp_path / "repo", files))
    assert code == 1
    assert "GATE-TR-UNPLANNED-SELF" in codes(report)


def test_scientific_not_applicable_without_a_reason_blocks(tmp_path: Path) -> None:
    files = default_files()
    files["verification/traceability.md"] = traceability(sci_reason="")
    code, report = run_gate(build_repo(tmp_path / "repo", files))
    assert code == 1
    assert "GATE-TR-APPLICABILITY-REASON" in codes(report)


def test_scientific_claim_without_an_evidence_record_blocks(tmp_path: Path) -> None:
    files = default_files()
    files["verification/traceability.md"] = traceability(
        sci_applicability="APPLICABLE",
        model_validation=EVIDENCE_RECORD,
        sci_rows=(
            row(
                "EV-404",
                "rats move at night",
                "P-1",
                "diffusion",
                "INFERRED",
                "docs/evidence/missing-record.md",
                "VERIFIED",
                "none",
            ),
        ),
    )
    code, report = run_gate(build_repo(tmp_path / "repo", files))
    assert code == 1
    assert "GATE-TR-EVIDENCE-UNRESOLVED" in codes(report)


def test_simulated_output_may_not_be_described_as_observed(tmp_path: Path) -> None:
    files = default_files()
    files["verification/traceability.md"] = traceability(
        sci_applicability="APPLICABLE",
        model_validation=EVIDENCE_RECORD,
        sci_rows=(
            row(
                "EV-1",
                "agents follow a biased walk",
                "P-1",
                "correlated random walk",
                "SIMULATED",
                EVIDENCE_RECORD,
                "PARTIALLY_VERIFIED",
                "reproduces the observed route qualitatively",
            ),
        ),
    )
    code, report = run_gate(build_repo(tmp_path / "repo", files))
    assert code == 1
    assert "GATE-TR-SIMULATED-AS-OBSERVED" in codes(report)


def test_unknown_parameter_may_not_be_closed_as_verified(tmp_path: Path) -> None:
    files = default_files()
    files["verification/traceability.md"] = traceability(
        sci_applicability="APPLICABLE",
        model_validation=EVIDENCE_RECORD,
        sci_rows=(
            row(
                "EV-2",
                "dispersal distance is unknown",
                "P-2",
                "random walk",
                "UNVERIFIED",
                EVIDENCE_RECORD,
                "VERIFIED",
                "none",
            ),
        ),
    )
    code, report = run_gate(build_repo(tmp_path / "repo", files))
    assert code == 1
    assert "GATE-TR-UNKNOWN-CLOSED" in codes(report)


def test_scientific_claim_with_an_evidence_record_passes(tmp_path: Path) -> None:
    files = default_files()
    files["verification/traceability.md"] = traceability(
        sci_applicability="APPLICABLE",
        model_validation=EVIDENCE_RECORD,
        sci_rows=(
            row(
                "EV-1",
                "agents follow a biased walk",
                "P-1",
                "correlated random walk",
                "SIMULATED",
                EVIDENCE_RECORD,
                "VERIFIED",
                "none",
            ),
        ),
    )
    repo = build_repo(tmp_path / "repo", files)
    (repo / EVIDENCE_RECORD).write_text(
        "# Model validation\n\nEV-1: seeded run, qualitative agreement.\n", encoding="utf-8"
    )
    code, report = run_gate(repo)
    assert code == 0, report["errors"]


def test_human_approval_required_without_a_decision_blocks(tmp_path: Path) -> None:
    files = default_files()
    files["verification/acceptance.md"] = acceptance(
        required="YES", trigger="NEW_SCIENTIFIC_ASSUMPTION", decision="PENDING"
    )
    code, report = run_gate(build_repo(tmp_path / "repo", files))
    assert code == 1
    assert "GATE-AC-NOT-APPROVED" in codes(report)


def test_recorded_human_approval_passes(tmp_path: Path) -> None:
    files = default_files()
    files["verification/acceptance.md"] = acceptance(
        required="YES", trigger="NEW_SCIENTIFIC_ASSUMPTION"
    )
    code, report = run_gate(build_repo(tmp_path / "repo", files))
    assert code == 0, report["errors"]


def test_agent_consensus_is_not_human_approval(tmp_path: Path) -> None:
    files = default_files()
    files["verification/acceptance.md"] = acceptance(consensus="yes")
    code, report = run_gate(build_repo(tmp_path / "repo", files))
    assert code == 1
    assert "GATE-AC-CONSENSUS" in codes(report)


def test_schema_drift_is_detected(tmp_path: Path) -> None:
    repo = build_repo(tmp_path / "repo")
    schema = repo / "openspec" / "schemas" / "evidence-driven" / "schema.yaml"
    text = schema.read_text(encoding="utf-8")
    start = text.index("  - id: adversarial-review")
    end = text.index("  - id: tasks")
    schema.write_text(text[:start] + text[end:], encoding="utf-8")
    code, report = run_gate(repo)
    assert code == 1
    assert "GATE-SCHEMA-DRIFT" in codes(report)


def test_unknown_change_is_a_usage_error(tmp_path: Path) -> None:
    repo = build_repo(tmp_path / "repo")
    result = subprocess.run(
        [sys.executable, str(GATE), "does-not-exist", "--repo-root", str(repo), "--json"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2
    assert "no such change" in result.stderr


def test_allow_no_change_is_a_clean_pass(tmp_path: Path) -> None:
    empty = tmp_path / "empty"
    (empty / "openspec" / "changes").mkdir(parents=True)
    result = subprocess.run(
        [sys.executable, str(GATE), "--repo-root", str(empty), "--allow-no-change"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "nothing to gate" in result.stdout


def test_weak_independence_without_a_waiver_blocks(tmp_path: Path) -> None:
    files = default_files()
    files["adversarial-review.md"] = adversarial_review(mechanism="NONE")
    repo = build_repo(tmp_path / "repo", files)
    code, report = run_gate(repo)
    assert code == 1
    assert "GATE-AR-INDEPENDENCE-WAIVER" in codes(report)


def test_unresolvable_waiver_reference_blocks(tmp_path: Path) -> None:
    files = default_files()
    files["adversarial-review.md"] = adversarial_review(
        mechanism="NONE", waiver="no/such/decision-record.md"
    )
    repo = build_repo(tmp_path / "repo", files)
    code, report = run_gate(repo)
    assert code == 1
    assert "GATE-AR-WAIVER-REFERENCE" in codes(report)


def test_weak_independence_with_a_human_waiver_passes_with_a_warning(tmp_path: Path) -> None:
    files = default_files()
    files["adversarial-review.md"] = adversarial_review(mechanism="NONE", waiver=EXTERNAL_WAIVER)
    files["verification/code-review.md"] = code_review(mechanism="NONE", waiver=EXTERNAL_WAIVER)
    repo = build_repo(tmp_path / "repo", files)
    code, report = run_gate(repo)
    assert code == 0, report["errors"]
    assert "GATE-AR-INDEPENDENCE-WEAK" in warnings(report)
    assert "GATE-CR-INDEPENDENCE-WEAK" in warnings(report)
    assert "GATE-AR-WAIVER-REFERENCE-EXTERNAL" in warnings(report)


def test_runtime_metadata_is_optional_provenance(tmp_path: Path) -> None:
    files = default_files()
    files["adversarial-review.md"] = adversarial_review(mechanism="SEPARATE_AGENT")
    files["verification/code-review.md"] = code_review(mechanism="SEPARATE_WORKTREE")
    repo = build_repo(tmp_path / "repo", files)
    code, report = run_gate(repo)
    assert code == 0, report["errors"]
    assert report["errors"] == []


def test_portable_external_approval_reference_is_accepted(tmp_path: Path) -> None:
    files = default_files()
    files["verification/acceptance.md"] = acceptance(
        required="YES", trigger="ARCHITECTURE_CHANGE", reference="tracker:RAT-42"
    )
    repo = build_repo(tmp_path / "repo", files)
    code, report = run_gate(repo)
    assert code == 0, report["errors"]
    assert "GATE-AC-REFERENCE-EXTERNAL" in warnings(report)


def test_gate_passes_with_no_agent_runtime_available(tmp_path: Path) -> None:
    repo = build_repo(tmp_path / "repo")
    code, report = run_gate(repo, env={"PATH": "/usr/bin:/bin"})
    assert code == 0, report["errors"]
    assert report["errors"] == []


OLD_PYTHON = "/usr/bin/python3"


def test_old_interpreter_fails_with_an_actionable_message() -> None:
    probe = [
        OLD_PYTHON,
        "-c",
        "import sys; raise SystemExit(0 if sys.version_info < (3, 10) else 1)",
    ]
    try:
        result = subprocess.run(probe, capture_output=True, check=False)
    except FileNotFoundError:
        pytest.skip("no pre-3.10 interpreter available")
    if result.returncode != 0:
        pytest.skip("no pre-3.10 interpreter available")
    old = subprocess.run(
        [OLD_PYTHON, str(GATE), "--help"], capture_output=True, text=True, check=False
    )
    assert old.returncode == 2
    assert "requires Python 3.10 or newer" in old.stderr


def test_wrong_review_type_blocks(tmp_path: Path) -> None:
    files = default_files()
    files["verification/code-review.md"] = code_review().replace(
        "Review type: INDEPENDENT_CODE_REVIEW", "Review type: ADVERSARIAL_REVIEW"
    )
    repo = build_repo(tmp_path / "repo", files)
    code, report = run_gate(repo)
    assert code == 1
    assert "GATE-CR-TYPE" in codes(report)
