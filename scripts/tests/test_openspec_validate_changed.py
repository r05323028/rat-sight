from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from .openspec_fixture import ROOT, prepare_repo

SCRIPT = ROOT / "scripts/openspec_validate_changed.py"


def openspec_available() -> bool:
    return bool(os.environ.get("RATSIGHT_OPENSPEC_BIN") or shutil.which("openspec"))


def run_script(
    repo: Path, *options: str, env: dict[str, str] | None = None
) -> tuple[subprocess.CompletedProcess[str], dict]:
    process_env = os.environ.copy()
    for name in ("GITHUB_EVENT_NAME", "GITHUB_BASE_REF", "GITHUB_EVENT_BEFORE"):
        process_env.pop(name, None)
    if env:
        process_env.update(env)
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--repo-root", str(repo), *options, "--json"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
        timeout=180,
        env=process_env,
    )
    return result, json.loads(result.stdout)


def git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
    return result


def git_repo_with_origin(tmp_path: Path) -> Path:
    """A committed fixture repo whose origin/main is fetchable, like CI with fetch-depth 0."""
    repo = prepare_repo(tmp_path)
    git(repo, "init", "-q", "-b", "main")
    git(repo, "config", "user.email", "fixture@example.test")
    git(repo, "config", "user.name", "Fixture")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "base")
    origin = tmp_path / "origin.git"
    subprocess.run(["git", "init", "-q", "--bare", str(origin)], check=True)
    git(repo, "remote", "add", "origin", str(origin))
    git(repo, "push", "-q", "-u", "origin", "main")
    return repo


def load_script_module():
    spec = importlib.util.spec_from_file_location("openspec_validate_changed", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_change_names_from_paths_ignores_archive_and_unrelated_paths() -> None:
    names = load_script_module().change_names_from_paths(
        [
            "openspec/changes/alpha/proposal.md",
            "openspec/changes/alpha/specs/x/spec.md",
            "openspec/changes/beta/tasks.md",
            "openspec/changes/archive/old/proposal.md",
            "openspec/changes/.hidden/proposal.md",
            "openspec/changes/README.md",
            "docs/notes.md",
        ]
    )
    assert names == ["alpha", "beta"]


def test_validate_all_passes_for_the_fixture(tmp_path: Path) -> None:
    if not openspec_available():
        pytest.skip("OpenSpec CLI unavailable")
    repo = prepare_repo(tmp_path)
    result, payload = run_script(repo, "--all")
    assert result.returncode == 0, payload["failures"]
    assert payload["changes"] == ["gate-fixture"]


def test_validate_all_blocks_a_broken_change(tmp_path: Path) -> None:
    if not openspec_available():
        pytest.skip("OpenSpec CLI unavailable")
    repo = prepare_repo(tmp_path)
    spec = repo / "openspec/changes/gate-fixture/specs/gate-fixture/spec.md"
    spec.write_text("# Spec Delta\n\n## ADDED Requirements\n\nNo scenarios here.\n")
    result, payload = run_script(repo, "--all")
    assert result.returncode == 1
    assert [failure["target"] for failure in payload["failures"]] == ["gate-fixture"]


def test_commit_range_limits_validation_to_touched_changes(tmp_path: Path) -> None:
    if not openspec_available() or not shutil.which("git"):
        pytest.skip("OpenSpec CLI or git unavailable")
    repo = prepare_repo(tmp_path)

    def git(*args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=False)

    git("init", "-q")
    git("config", "user.email", "fixture@example.test")
    git("config", "user.name", "Fixture")
    git("add", "-A")
    git("commit", "-qm", "base")
    (repo / "README.md").write_text("unrelated\n")
    second = git("add", "-A")
    assert second.returncode == 0
    git("commit", "-qm", "docs only")
    result, payload = run_script(repo, "--base", "HEAD~1")
    assert result.returncode == 0, payload["failures"]
    assert payload["changes"] == []
    assert payload["evaluated"] == 0
    assert "no OpenSpec change paths" in payload["note"]

    target = repo / "openspec/changes/gate-fixture/tasks.md"
    target.write_text(target.read_text() + "- [x] 9.9 Fixture follow-up.\n")
    git("add", "-A")
    git("commit", "-qm", "change artifact")
    result, payload = run_script(repo, "--base", "HEAD~1")
    assert result.returncode == 0, payload["failures"]
    assert payload["changes"] == ["gate-fixture"]
    assert payload["evaluated"] == 1


def test_pull_request_uses_origin_base(tmp_path: Path) -> None:
    if not openspec_available() or not shutil.which("git"):
        pytest.skip("OpenSpec CLI or git unavailable")
    repo = git_repo_with_origin(tmp_path)
    git(repo, "checkout", "-q", "-b", "feature")
    target = repo / "openspec/changes/gate-fixture/tasks.md"
    target.write_text(target.read_text() + "- [x] 9.9 Fixture follow-up.\n")
    git(repo, "commit", "-qam", "change artifact")
    result, payload = run_script(
        repo, env={"GITHUB_EVENT_NAME": "pull_request", "GITHUB_BASE_REF": "main"}
    )
    assert result.returncode == 0, payload["failures"]
    assert payload["changes"] == ["gate-fixture"]
    assert payload["base"] == "origin/main"
    assert payload["base_source"] == "pull request base"


def test_pull_request_without_openspec_changes_reports_zero(tmp_path: Path) -> None:
    if not openspec_available() or not shutil.which("git"):
        pytest.skip("OpenSpec CLI or git unavailable")
    repo = git_repo_with_origin(tmp_path)
    git(repo, "checkout", "-q", "-b", "docs")
    (repo / "README.md").write_text("unrelated\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "docs only")
    result, payload = run_script(
        repo, env={"GITHUB_EVENT_NAME": "pull_request", "GITHUB_BASE_REF": "main"}
    )
    assert result.returncode == 0, payload["failures"]
    assert payload["changes"] == []
    assert payload["evaluated"] == 0
    assert payload["checks"] == ["schema evidence-driven"]


def test_pull_request_without_base_ref_fails(tmp_path: Path) -> None:
    repo = git_repo_with_origin(tmp_path)
    result, payload = run_script(repo, env={"GITHUB_EVENT_NAME": "pull_request"})
    assert result.returncode == 2
    assert payload["failed"] is True
    assert payload["changes"] is None
    assert "GITHUB_BASE_REF" in result.stderr


def test_push_event_uses_previous_commit(tmp_path: Path) -> None:
    if not openspec_available() or not shutil.which("git"):
        pytest.skip("OpenSpec CLI or git unavailable")
    repo = git_repo_with_origin(tmp_path)
    before = git(repo, "rev-parse", "HEAD").stdout.strip()
    target = repo / "openspec/changes/gate-fixture/tasks.md"
    target.write_text(target.read_text() + "- [x] 9.8 Fixture follow-up.\n")
    git(repo, "commit", "-qam", "change artifact")
    result, payload = run_script(
        repo, env={"GITHUB_EVENT_NAME": "push", "GITHUB_EVENT_BEFORE": before}
    )
    assert result.returncode == 0, payload["failures"]
    assert payload["changes"] == ["gate-fixture"]
    assert payload["base_source"] == "push event before"


def test_zero_before_sha_falls_back_to_default_branch(tmp_path: Path) -> None:
    if not openspec_available() or not shutil.which("git"):
        pytest.skip("OpenSpec CLI or git unavailable")
    repo = git_repo_with_origin(tmp_path)
    target = repo / "openspec/changes/gate-fixture/tasks.md"
    target.write_text(target.read_text() + "- [x] 9.7 Fixture follow-up.\n")
    git(repo, "commit", "-qam", "change artifact")
    result, payload = run_script(
        repo,
        env={"GITHUB_EVENT_NAME": "push", "GITHUB_EVENT_BEFORE": "0" * 40},
    )
    assert result.returncode == 0, payload["failures"]
    assert payload["base"] == "origin/main"
    assert payload["base_source"] == "default branch"
    assert payload["changes"] == ["gate-fixture"]


def test_shallow_checkout_cannot_report_success(tmp_path: Path) -> None:
    if not shutil.which("git"):
        pytest.skip("git unavailable")
    repo = git_repo_with_origin(tmp_path)
    shallow = tmp_path / "shallow"
    subprocess.run(
        ["git", "clone", "-q", "--depth", "1", "file://" + str(repo), str(shallow)],
        check=True,
    )
    result, payload = run_script(shallow)
    assert result.returncode == 2
    assert payload["failed"] is True
    assert payload["changes"] is None
    assert payload["evaluated"] == 0
    assert "resolves to HEAD" in result.stderr
    assert "fetch-depth" in result.stderr


def test_missing_base_fails_explicitly(tmp_path: Path) -> None:
    repo = git_repo_with_origin(tmp_path)
    result, payload = run_script(repo, "--base", "origin/does-not-exist")
    assert result.returncode == 2
    assert payload["failed"] is True
    assert "does not resolve" in result.stderr
