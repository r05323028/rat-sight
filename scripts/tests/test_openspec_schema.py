from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from .openspec_fixture import prepare_repo


def openspec_binary() -> str | None:
    return os.environ.get("RATSIGHT_OPENSPEC_BIN") or shutil.which("openspec")


def run_cli(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    binary = openspec_binary()
    if binary is None:
        pytest.skip("OpenSpec CLI unavailable")
    return subprocess.run(
        [binary, *args], cwd=repo, capture_output=True, text=True, check=False, timeout=90
    )


def test_installed_cli_validates_custom_schema(tmp_path: Path) -> None:
    repo = prepare_repo(tmp_path)
    result = run_cli(repo, "schema", "validate", "evidence-driven")
    assert result.returncode == 0, result.stdout + result.stderr


def test_cli_validates_change_and_exposes_native_requirement_name(tmp_path: Path) -> None:
    repo = prepare_repo(tmp_path)
    result = run_cli(repo, "validate", "gate-fixture")
    assert result.returncode == 0, result.stdout + result.stderr
    shown = run_cli(repo, "show", "gate-fixture", "--json", "--deltas-only")
    assert shown.returncode == 0, shown.stdout + shown.stderr
    payload = json.loads(shown.stdout)
    assert payload["deltas"][0]["spec"] == "gate-fixture"
    assert payload["deltas"][0]["requirements"][0]["name"] == (
        "Fixture capability returns a constant"
    )


def test_cli_enforces_adversarial_artifact_and_task_dependency(tmp_path: Path) -> None:
    repo = prepare_repo(tmp_path)
    status = run_cli(repo, "status", "--change", "gate-fixture", "--json")
    assert status.returncode == 0, status.stdout + status.stderr
    payload = json.loads(status.stdout)
    assert payload["schemaName"] == "evidence-driven"
    assert "adversarial-review" in payload["artifactPaths"]
    assert payload["applyRequires"] == ["tasks"]

    change = repo / "openspec/changes/gate-fixture"
    shutil.rmtree(change / "specs")
    (change / "design.md").unlink()
    (change / "adversarial-review.md").unlink()
    instructions = run_cli(repo, "instructions", "tasks", "--change", "gate-fixture")
    assert instructions.returncode == 0, instructions.stdout + instructions.stderr
    missing = next(line for line in instructions.stdout.splitlines() if "Missing:" in line)
    for artifact in ("specs", "design", "adversarial-review"):
        assert artifact in missing


def test_cli_preserves_skip_specs_compatibility(tmp_path: Path) -> None:
    repo = prepare_repo(tmp_path)
    change = repo / "openspec/changes/gate-fixture"
    (change / ".openspec.yaml").write_text(
        "schema: evidence-driven\nskip_specs: true\n", encoding="utf-8"
    )
    shutil.rmtree(change / "specs")
    result = run_cli(repo, "validate", "gate-fixture")
    assert result.returncode == 0, result.stdout + result.stderr
    shown = run_cli(repo, "show", "gate-fixture", "--json", "--deltas-only")
    assert shown.returncode == 0, shown.stdout + shown.stderr
    assert json.loads(shown.stdout)["deltaCount"] == 0
