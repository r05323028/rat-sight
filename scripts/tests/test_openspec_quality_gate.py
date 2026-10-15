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


def change_dir(repo: Path) -> Path:
    return repo / "openspec/changes" / CHANGE


def read_state(repo: Path) -> dict[str, Any]:
    return json.loads((change_dir(repo) / "verification/gate.json").read_text())


def save_state(repo: Path, state: dict[str, Any]) -> None:
    (change_dir(repo) / "verification/gate.json").write_text(json.dumps(state, indent=2) + "\n")


def run_gate(
    repo: Path, *options: str, env: dict[str, str] | None = None
) -> tuple[subprocess.CompletedProcess[str], dict[str, Any]]:
    process_env = os.environ.copy()
    if env:
        process_env.update(env)
    result = subprocess.run(
        [sys.executable, str(SCRIPT), CHANGE, "--repo-root", str(repo), *options, "--json"],
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
    result, report = run_gate(repo, "--skip-openspec")
    assert result.returncode == 0, report["errors"]


@pytest.mark.parametrize("report_path", ["adversarial-review.md", "verification/code-review.md"])
def test_missing_mandatory_review_record_blocks(tmp_path: Path, report_path: str) -> None:
    repo = prepare_repo(tmp_path)
    (change_dir(repo) / report_path).unlink()
    result, report = run_gate(repo, "--skip-openspec")
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
                "status": "ACCEPTED_RISK",
                "residual_risk": "Retained fixture risk.",
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
    result, report = run_gate(repo, "--skip-openspec")
    assert result.returncode == 1
    assert "GATE-CR-BLOCKING" in error_codes(report)


def test_approved_nonblocking_risk_needs_exact_finding_and_passes(tmp_path: Path) -> None:
    repo = prepare_repo(tmp_path)
    state = accepted_risk_state(repo)
    state["approval"] = approval(["CR-1"])
    save_state(repo, state)
    (change_dir(repo) / "verification/acceptance.md").write_text("Synthetic decision for CR-1.\n")
    result, report = run_gate(repo, "--skip-openspec")
    assert result.returncode == 0, report["errors"]


def test_nonblocking_accepted_risk_without_approval_blocks(tmp_path: Path) -> None:
    repo = prepare_repo(tmp_path)
    save_state(repo, accepted_risk_state(repo))
    result, report = run_gate(repo, "--skip-openspec")
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
    result, report = run_gate(repo, "--skip-openspec")
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
    result, report = run_gate(repo, "--skip-openspec")
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
    result, report = run_gate(repo, "--skip-openspec")
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
    result, report = run_gate(repo, "--skip-openspec")
    assert result.returncode == 0, report["errors"]


def test_required_human_approval_needs_record_and_valid_decision(tmp_path: Path) -> None:
    repo = prepare_repo(tmp_path)
    state = read_state(repo)
    state["approval"] = approval()
    save_state(repo, state)
    result, report = run_gate(repo, "--skip-openspec")
    assert result.returncode == 1
    assert "GATE-APPROVAL-RECORD" in error_codes(report)


def test_valid_recorded_human_approval_passes(tmp_path: Path) -> None:
    repo = prepare_repo(tmp_path)
    state = read_state(repo)
    state["approval"] = approval()
    save_state(repo, state)
    (change_dir(repo) / "verification/acceptance.md").write_text("Synthetic decision receipt.\n")
    result, report = run_gate(repo, "--skip-openspec")
    assert result.returncode == 0, report["errors"]


def test_gate_runs_without_openspec_or_agent_runtime(tmp_path: Path) -> None:
    repo = prepare_repo(tmp_path)
    empty_path = tmp_path / "empty-bin"
    empty_path.mkdir()
    result, report = run_gate(
        repo,
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
