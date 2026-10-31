from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from .openspec_fixture import ROOT, prepare_repo

SCRIPT = ROOT / "scripts/openspec_quality_gate.py"
CHANGE = "gate-fixture"


def change_dir(repo: Path, name: str = CHANGE) -> Path:
    return repo / "openspec/changes" / name


def read_state(repo: Path, name: str = CHANGE) -> dict[str, Any]:
    return json.loads((change_dir(repo, name) / "verification/gate.json").read_text())


LEGACY_CHANGE = "stabilize-local-analyst-workflow"


def rename_change(repo: Path, name: str) -> None:
    change_dir(repo).rename(change_dir(repo, name))


def save_state(repo: Path, state: dict[str, Any], name: str = CHANGE) -> None:
    target = change_dir(repo, name) / "verification/gate.json"
    target.write_text(json.dumps(state, indent=2) + "\n")


def run_gate(
    repo: Path, *options: str, env: dict[str, str] | None = None, name: str = CHANGE
) -> tuple[subprocess.CompletedProcess[str], dict[str, Any]]:
    if "--skip-openspec" not in options and not (
        os.environ.get("RATSIGHT_OPENSPEC_BIN") or shutil.which("openspec")
    ):
        pytest.skip("OpenSpec CLI unavailable; readiness requires it")
    process_env = os.environ.copy()
    if env:
        process_env.update(env)
    result = subprocess.run(
        [sys.executable, str(SCRIPT), name, "--repo-root", str(repo), *options, "--json"],
        cwd=repo,
        env=process_env,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    return result, json.loads(result.stdout)


def error_codes(report: dict[str, Any]) -> set[str]:
    return {item["code"] for item in report["errors"]}


def approval(findings: list[str] | None = None) -> dict[str, Any]:
    return {
        "required": True,
        "trigger": "ACCEPTANCE_EXCEPTION",
        "decision": "APPROVED",
        "approver": "fixture-human",
        "reference": "synthetic-decision-reference",
        "scope": "Fixture decision",
        "findings": findings or [],
    }


def test_complete_change_passes_without_context_fields_and_acceptance_is_optional(
    tmp_path: Path,
) -> None:
    if not (os.environ.get("RATSIGHT_OPENSPEC_BIN") or shutil.which("openspec")):
        pytest.skip("OpenSpec CLI unavailable")
    repo = prepare_repo(tmp_path)
    result, report = run_gate(repo)
    assert result.returncode == 0, report["errors"]
    assert report["passed"] is True
    assert not (change_dir(repo) / "verification/acceptance.md").exists()


def test_incomplete_required_tasks_block_gate(tmp_path: Path) -> None:
    repo = prepare_repo(tmp_path)
    task_file = change_dir(repo) / "tasks.md"
    task_file.write_text(
        task_file.read_text(encoding="utf-8") + "- [ ] incomplete mandatory work\n",
        encoding="utf-8",
    )
    result, report = run_gate(repo)
    assert result.returncode == 1
    assert "GATE-TASKS-INCOMPLETE" in error_codes(report)


def test_missing_required_tasks_block_gate(tmp_path: Path) -> None:
    repo = prepare_repo(tmp_path)
    (change_dir(repo) / "tasks.md").unlink()
    result, report = run_gate(repo)
    assert result.returncode == 1
    assert "GATE-TASKS-MISSING" in error_codes(report)


def test_excluded_sections_without_unchecked_boxes_do_not_block(tmp_path: Path) -> None:
    repo = prepare_repo(tmp_path)
    task_file = change_dir(repo) / "tasks.md"
    task_file.write_text(
        task_file.read_text(encoding="utf-8")
        + "\n## Future follow-up\n- [x] already handled elsewhere\n- Archive later.\n",
        encoding="utf-8",
    )
    result, report = run_gate(repo)
    assert result.returncode == 0, report["errors"]


def test_gate_blocks_when_openspec_validation_fails(tmp_path: Path) -> None:
    if not (os.environ.get("RATSIGHT_OPENSPEC_BIN") or shutil.which("openspec")):
        pytest.skip("OpenSpec CLI unavailable")
    repo = prepare_repo(tmp_path)
    (change_dir(repo) / ".openspec.yaml").write_text("schema: missing-schema\n")
    result, report = run_gate(repo)
    assert result.returncode == 1
    assert any(error["code"].startswith("GATE-OPENSPEC") for error in report["errors"])


def test_same_reviewer_and_subject_identities_do_not_block(tmp_path: Path) -> None:
    repo = prepare_repo(tmp_path)
    state = read_state(repo)
    state["reviews"]["adversarial"].update({"reviewer": "same-person", "author": "same-person"})
    state["reviews"]["code"].update({"reviewer": "same-person", "implementer": "same-person"})
    save_state(repo, state)
    result, report = run_gate(repo)
    assert result.returncode == 0, report["errors"]


@pytest.mark.parametrize("report_path", ["adversarial-review.md", "verification/code-review.md"])
def test_missing_mandatory_review_record_blocks(tmp_path: Path, report_path: str) -> None:
    repo = prepare_repo(tmp_path)
    (change_dir(repo) / report_path).unlink()
    result, report = run_gate(repo)
    assert result.returncode == 1
    expected = "GATE-AR-MISSING" if report_path.startswith("adversarial") else "GATE-CR-MISSING"
    assert expected in error_codes(report)


def accepted_risk_state(repo: Path, severity: str = "MAJOR") -> dict[str, Any]:
    state = read_state(repo)
    state["reviews"]["code"].update(
        decision="PASS_WITH_WARNINGS",
        findings=[
            {
                "id": "CR-1",
                "severity": severity,
                "verification": "SUSPECTED",
                "status": "ACCEPTED_RISK",
                "residual_risk": "Retained fixture risk.",
                "evidence": "Synthetic fixture evidence reference.",
            }
        ],
    )
    return state


def test_blocking_finding_cannot_be_waived_by_approval(tmp_path: Path) -> None:
    repo = prepare_repo(tmp_path)
    state = accepted_risk_state(repo, "BLOCKING")
    state["approval"] = approval(["CR-1"])
    save_state(repo, state)
    (change_dir(repo) / "verification/acceptance.md").write_text("Synthetic receipt.\n")
    result, report = run_gate(repo)
    assert result.returncode == 1
    assert "GATE-CR-BLOCKING" in error_codes(report)


def test_approved_nonblocking_risk_needs_exact_finding_and_passes(tmp_path: Path) -> None:
    repo = prepare_repo(tmp_path)
    state = accepted_risk_state(repo)
    state["approval"] = approval(["CR-1"])
    save_state(repo, state)
    (change_dir(repo) / "verification/acceptance.md").write_text("Synthetic decision for CR-1.\n")
    result, report = run_gate(repo)
    assert result.returncode == 0, report["errors"]


def test_nonblocking_accepted_risk_without_approval_blocks(tmp_path: Path) -> None:
    repo = prepare_repo(tmp_path)
    save_state(repo, accepted_risk_state(repo))
    result, report = run_gate(repo)
    assert result.returncode == 1
    assert "GATE-APPROVAL-MISSING" in error_codes(report)


def test_missing_requirement_mapping_blocks(tmp_path: Path) -> None:
    if not (os.environ.get("RATSIGHT_OPENSPEC_BIN") or shutil.which("openspec")):
        pytest.skip("OpenSpec CLI unavailable")
    repo = prepare_repo(tmp_path)
    state = read_state(repo)
    state["engineering"] = []
    save_state(repo, state)
    result, report = run_gate(repo)
    assert result.returncode == 1
    assert "GATE-TRACE-COVERAGE" in error_codes(report)


@pytest.mark.parametrize(
    ("runs", "expected"),
    [
        ([], "GATE-VERIFICATION-MISSING"),
        (
            [
                {
                    "id": "fixture-test-run",
                    "command": "pytest",
                    "exit_code": 1,
                    "result": "failed",
                    "reference": "fixture",
                }
            ],
            "GATE-VERIFICATION-FAILED",
        ),
    ],
)
def test_missing_or_failed_verification_blocks(
    tmp_path: Path, runs: list[dict[str, Any]], expected: str
) -> None:
    repo = prepare_repo(tmp_path)
    state = read_state(repo)
    state["verification"] = runs
    save_state(repo, state)
    result, report = run_gate(repo)
    assert result.returncode == 1
    assert expected in error_codes(report)


def science_claim(identifier: str, source: str) -> dict[str, Any]:
    return {
        "evidence_id": identifier,
        "source": source,
        "assumption": "Synthetic fixture assumption only.",
        "parameter": "fixture-only parameter",
        "model": "No biological model; test data only.",
        "data_class": "SIMULATED",
        "status": "VERIFIED",
        "validation": ["fixture-test-run"],
    }


def test_applicable_science_requires_traceability(tmp_path: Path) -> None:
    repo = prepare_repo(tmp_path)
    state = read_state(repo)
    state["science"] = {"applicable": True, "claims": []}
    save_state(repo, state)
    result, report = run_gate(repo)
    assert result.returncode == 1
    assert "GATE-SCIENCE-MISSING" in error_codes(report)


@pytest.mark.parametrize(
    ("identifier", "source"),
    [("EV-10", "docs/evidence/EV-1.md"), ("EV-1", "docs/evidence/EV-10.md")],
)
def test_evidence_source_must_match_exact_id_and_exist(
    tmp_path: Path, identifier: str, source: str
) -> None:
    repo = prepare_repo(tmp_path)
    state = read_state(repo)
    state["science"] = {
        "applicable": True,
        "claims": [science_claim(identifier, source)],
    }
    save_state(repo, state)
    result, report = run_gate(repo)
    assert result.returncode == 1
    assert "GATE-SCIENCE-SOURCE" in error_codes(report)


def test_explicit_simulated_science_source_passes(tmp_path: Path) -> None:
    repo = prepare_repo(tmp_path)
    state = read_state(repo)
    state["science"] = {
        "applicable": True,
        "claims": [science_claim("EV-1", "docs/evidence/EV-1.md")],
    }
    save_state(repo, state)
    result, report = run_gate(repo)
    assert result.returncode == 0, report["errors"]


def test_required_human_approval_needs_record_and_valid_decision(tmp_path: Path) -> None:
    repo = prepare_repo(tmp_path)
    state = read_state(repo)
    state["approval"] = approval()
    save_state(repo, state)
    result, report = run_gate(repo)
    assert result.returncode == 1
    assert "GATE-APPROVAL-RECORD" in error_codes(report)


def test_valid_recorded_human_approval_passes(tmp_path: Path) -> None:
    repo = prepare_repo(tmp_path)
    state = read_state(repo)
    state["approval"] = approval()
    save_state(repo, state)
    (change_dir(repo) / "verification/acceptance.md").write_text("Synthetic decision receipt.\n")
    result, report = run_gate(repo)
    assert result.returncode == 0, report["errors"]


def test_gate_runs_without_openspec_or_agent_runtime(tmp_path: Path) -> None:
    repo = prepare_repo(tmp_path)
    empty_path = tmp_path / "empty-bin"
    empty_path.mkdir()
    result, report = run_gate(
        repo,
        "--stage",
        "planning",
        "--skip-openspec",
        env={"PATH": str(empty_path), "RATSIGHT_OPENSPEC_BIN": ""},
    )
    assert result.returncode == 0, report["errors"]
    assert any(item["code"] == "GATE-OPENSPEC-SKIPPED" for item in report["warnings"])


def test_no_active_change_is_a_valid_repository_state(tmp_path: Path) -> None:
    repo = prepare_repo(tmp_path)
    shutil.rmtree(repo / "openspec/changes/gate-fixture")
    command = [sys.executable, str(SCRIPT), "--repo-root", str(repo)]
    missing = subprocess.run(command, cwd=repo, capture_output=True, text=True, check=False)
    allowed = subprocess.run(
        [*command, "--allow-no-change"], cwd=repo, capture_output=True, text=True, check=False
    )
    assert missing.returncode == 2
    assert allowed.returncode == 0


def test_v3_requires_finding_verification_axis(tmp_path: Path) -> None:
    repo = prepare_repo(tmp_path)
    state = accepted_risk_state(repo)
    state["reviews"]["code"]["findings"][0].pop("verification")
    state["approval"] = approval(["CR-1"])
    save_state(repo, state)
    (change_dir(repo) / "verification/acceptance.md").write_text("Synthetic decision.\n")
    result, report = run_gate(repo)
    assert result.returncode == 1
    assert "GATE-CR-FINDING-VERIFICATION" in error_codes(report)


def test_v3_rejects_unknown_verification_state(tmp_path: Path) -> None:
    repo = prepare_repo(tmp_path)
    state = accepted_risk_state(repo)
    state["reviews"]["code"]["findings"][0]["verification"] = "PROBABLY"
    save_state(repo, state)
    result, report = run_gate(repo)
    assert result.returncode == 1
    assert "GATE-CR-FINDING-VERIFICATION" in error_codes(report)


def test_v3_blocking_finding_requires_evidence(tmp_path: Path) -> None:
    repo = prepare_repo(tmp_path)
    state = accepted_risk_state(repo, "BLOCKING")
    finding = state["reviews"]["code"]["findings"][0]
    finding["status"] = "RESOLVED"
    finding.pop("evidence")
    save_state(repo, state)
    result, report = run_gate(repo)
    assert result.returncode == 1
    assert "GATE-CR-FINDING-EVIDENCE" in error_codes(report)


def test_v3_suspected_finding_with_evidence_passes(tmp_path: Path) -> None:
    repo = prepare_repo(tmp_path)
    state = read_state(repo)
    state["reviews"]["adversarial"].update(
        decision="PASS_WITH_WARNINGS",
        findings=[
            {
                "id": "AR-1",
                "severity": "MINOR",
                "verification": "SUSPECTED",
                "status": "OPEN",
                "evidence": "Read services/api/src/fixture.py:1 and could not reproduce.",
            }
        ],
    )
    save_state(repo, state)
    result, report = run_gate(repo)
    assert result.returncode == 0, report["errors"]


def test_v3_partially_verified_blocks_readiness(tmp_path: Path) -> None:
    repo = prepare_repo(tmp_path)
    state = read_state(repo)
    state["engineering"][0].update(status="PARTIALLY_VERIFIED", gap="Browser path unverified.")
    save_state(repo, state)
    result, report = run_gate(repo)
    assert result.returncode == 1
    assert "GATE-TRACE-PARTIAL" in error_codes(report)


def test_legacy_partially_verified_only_warns(tmp_path: Path) -> None:
    repo = prepare_repo(tmp_path)
    state = read_state(repo)
    rename_change(repo, LEGACY_CHANGE)
    state["schema_version"] = 2
    state["engineering"][0].update(status="PARTIALLY_VERIFIED", gap="Browser path unverified.")
    save_state(repo, state, LEGACY_CHANGE)
    result, report = run_gate(repo, name=LEGACY_CHANGE)
    assert result.returncode == 0, report["errors"]
    assert any(item["code"] == "GATE-TRACE-PARTIAL" for item in report["warnings"])
    assert any(item["code"] == "GATE-RECORD-LEGACY" for item in report["warnings"])
    assert "GATE-RECORD-VERSION-LEGACY" not in error_codes(report)


def test_v3_not_applicable_blocks_for_changed_requirement(tmp_path: Path) -> None:
    if not (os.environ.get("RATSIGHT_OPENSPEC_BIN") or shutil.which("openspec")):
        pytest.skip("OpenSpec CLI unavailable")
    repo = prepare_repo(tmp_path)
    state = read_state(repo)
    state["engineering"][0].update(status="NOT_APPLICABLE", gap="Nothing to check.")
    save_state(repo, state)
    result, report = run_gate(repo)
    assert result.returncode == 1
    assert "GATE-TRACE-EXCEPTION" in error_codes(report)


def test_v3_not_applicable_allowed_for_removed_requirement(tmp_path: Path) -> None:
    if not (os.environ.get("RATSIGHT_OPENSPEC_BIN") or shutil.which("openspec")):
        pytest.skip("OpenSpec CLI unavailable")
    repo = prepare_repo(tmp_path)
    delta = change_dir(repo) / "specs/gate-fixture/spec.md"
    delta.write_text(
        delta.read_text(encoding="utf-8")
        + "\n## REMOVED Requirements\n\n### Requirement: Removed fixture capability\n\n"
        + "**Reason**: Synthetic removal.\n\n**Migration**: Use the stable constant.\n"
    )
    state = read_state(repo)
    state["engineering"].append(
        {
            "requirement": "gate-fixture#Removed fixture capability",
            "status": "NOT_APPLICABLE",
            "gap": "Requirement is removed by this change.",
        }
    )
    save_state(repo, state)
    result, report = run_gate(repo)
    assert result.returncode == 0, report["errors"]


@pytest.mark.parametrize(
    "reference",
    ["/etc/hosts", "docs/evidence/missing.md", "verification/gate.json", "../outside.md"],
)
def test_v3_rejects_unresolvable_references(tmp_path: Path, reference: str) -> None:
    repo = prepare_repo(tmp_path)
    state = read_state(repo)
    state["verification"][0]["reference"] = reference
    save_state(repo, state)
    result, report = run_gate(repo)
    assert result.returncode == 1
    assert "GATE-VERIFICATION-REFERENCE" in error_codes(report)


def test_v3_accepts_repository_and_ci_references(tmp_path: Path) -> None:
    repo = prepare_repo(tmp_path)
    state = read_state(repo)
    state["verification"][0]["reference"] = "docs/evidence/EV-1.md"
    state["verification"].append(
        {
            "id": "ci-run",
            "command": "ci:unit",
            "exit_code": 0,
            "result": "passed in CI",
            "reference": "ci:workflow-run-42",
        }
    )
    state["engineering"][0]["verification"].append("ci-run")
    save_state(repo, state)
    result, report = run_gate(repo)
    assert result.returncode == 0, report["errors"]


def test_legacy_reference_problem_only_warns(tmp_path: Path) -> None:
    repo = prepare_repo(tmp_path)
    state = read_state(repo)
    rename_change(repo, LEGACY_CHANGE)
    state["schema_version"] = 2
    state["verification"][0]["reference"] = "/tmp/stale-evidence.txt"
    save_state(repo, state, LEGACY_CHANGE)
    result, report = run_gate(repo, name=LEGACY_CHANGE)
    assert result.returncode == 0, report["errors"]
    assert any(item["code"] == "GATE-VERIFICATION-REFERENCE" for item in report["warnings"])


def test_new_change_cannot_declare_legacy_version(tmp_path: Path) -> None:
    repo = prepare_repo(tmp_path)
    state = read_state(repo)
    state["schema_version"] = 2
    state["engineering"][0].update(status="PARTIALLY_VERIFIED", gap="Browser path unverified.")
    save_state(repo, state)
    result, report = run_gate(repo)
    assert result.returncode == 1
    assert "GATE-RECORD-VERSION-LEGACY" in error_codes(report)
    assert "GATE-TRACE-PARTIAL" in error_codes(report)


def test_legacy_change_can_opt_into_current_checks(tmp_path: Path) -> None:
    repo = prepare_repo(tmp_path)
    state = read_state(repo)
    rename_change(repo, LEGACY_CHANGE)
    state["schema_version"] = 3
    state["engineering"][0].update(status="PARTIALLY_VERIFIED", gap="Browser path unverified.")
    save_state(repo, state, LEGACY_CHANGE)
    result, report = run_gate(repo, name=LEGACY_CHANGE)
    assert result.returncode == 1
    assert "GATE-TRACE-PARTIAL" in error_codes(report)
    assert not any(item["code"] == "GATE-RECORD-LEGACY" for item in report["warnings"])


def test_readiness_rejects_skipped_requirement_coverage(tmp_path: Path) -> None:
    repo = prepare_repo(tmp_path)
    result, report = run_gate(repo, "--skip-openspec")
    assert result.returncode == 1
    assert "GATE-OPENSPEC-SKIPPED" in error_codes(report)
    message = next(
        item["message"] for item in report["errors"] if item["code"] == "GATE-OPENSPEC-SKIPPED"
    )
    assert "--stage planning" in message


def test_unknown_record_version_blocks(tmp_path: Path) -> None:
    repo = prepare_repo(tmp_path)
    state = read_state(repo)
    state["schema_version"] = 9
    save_state(repo, state)
    result, report = run_gate(repo)
    assert result.returncode == 1
    assert "GATE-RECORD-VERSION" in error_codes(report)


def test_missing_record_version_blocks(tmp_path: Path) -> None:
    repo = prepare_repo(tmp_path)
    state = read_state(repo)
    state.pop("schema_version")
    save_state(repo, state)
    result, report = run_gate(repo)
    assert result.returncode == 1
    assert "GATE-RECORD-VERSION" in error_codes(report)


def test_unchecked_task_under_excluded_heading_blocks(tmp_path: Path) -> None:
    repo = prepare_repo(tmp_path)
    tasks = change_dir(repo) / "tasks.md"
    tasks.write_text(
        tasks.read_text(encoding="utf-8") + "\n## Out of Scope\n\n- [ ] hidden unfinished work\n",
        encoding="utf-8",
    )
    result, report = run_gate(repo)
    assert result.returncode == 1
    assert "GATE-TASKS-EXCLUDED" in error_codes(report)


def test_excluded_plain_bullets_are_allowed(tmp_path: Path) -> None:
    repo = prepare_repo(tmp_path)
    tasks = change_dir(repo) / "tasks.md"
    tasks.write_text(
        tasks.read_text(encoding="utf-8")
        + "\n## Workflow follow-up\n\n- Archive after acceptance.\n",
        encoding="utf-8",
    )
    result, report = run_gate(repo)
    assert result.returncode == 0, report["errors"]


def test_preflight_blocks_empty_adversarial_review(tmp_path: Path) -> None:
    repo = prepare_repo(tmp_path)
    (change_dir(repo) / "adversarial-review.md").write_text("", encoding="utf-8")
    result, report = run_gate(repo, "--skip-openspec", "--stage", "planning")
    assert result.returncode == 1
    assert "GATE-AR-MISSING" in error_codes(report)


def test_preflight_blocks_unresolved_blocking_finding(tmp_path: Path) -> None:
    repo = prepare_repo(tmp_path)
    state = read_state(repo)
    state["reviews"]["adversarial"].update(
        decision="PASS_WITH_WARNINGS",
        findings=[
            {
                "id": "AR-1",
                "severity": "BLOCKING",
                "verification": "VERIFIED",
                "status": "OPEN",
                "evidence": "Reproduced with scripts/tests/test_openspec_quality_gate.py.",
            }
        ],
    )
    save_state(repo, state)
    result, report = run_gate(repo, "--skip-openspec", "--stage", "planning")
    assert result.returncode == 1
    assert "GATE-AR-BLOCKING" in error_codes(report)


def test_preflight_ignores_implementation_evidence(tmp_path: Path) -> None:
    repo = prepare_repo(tmp_path)
    (change_dir(repo) / "tasks.md").unlink()
    state = read_state(repo)
    state["verification"] = []
    state["engineering"] = []
    save_state(repo, state)
    planning, planning_report = run_gate(repo, "--skip-openspec", "--stage", "planning")
    assert planning.returncode == 0, planning_report["errors"]
    readiness, readiness_report = run_gate(repo)
    assert readiness.returncode == 1
    assert {"GATE-TASKS-MISSING", "GATE-VERIFICATION-MISSING"} <= error_codes(readiness_report)
