from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parents[1] / "change_acceptance.py"
spec = importlib.util.spec_from_file_location("change_acceptance", SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def git_commit(root: Path, message: str) -> None:
    subprocess.run(["git", "add", "-A"], cwd=root, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", message], cwd=root, check=True, capture_output=True)


def repo(tmp_path: Path) -> tuple[Path, Path]:
    root = tmp_path / "repo"
    change = root / "openspec/changes/example"
    (change / "verification").mkdir(parents=True)
    (root / "src").mkdir(parents=True)
    (root / "services/api/src/ratsight_api/api").mkdir(parents=True)
    (root / "tests").mkdir()
    (root / "Makefile").write_text("", encoding="utf-8")
    (root / "openspec/config.yaml").write_text("", encoding="utf-8")
    (root / "src/application.py").write_text("value = 1\n", encoding="utf-8")
    (root / "services/api/src/ratsight_api/api/schemas.py").write_text(
        "class Request: pass\n", encoding="utf-8"
    )
    (root / "tests/test_application.py").write_text("def test_value(): pass\n", encoding="utf-8")
    (change / "proposal.md").write_text("# Example\n\nSmall workflow change.\n", encoding="utf-8")
    (change / "tasks.md").write_text(
        "- [x] required implementation\n\n## Future follow-up\n- Archive later.\n", encoding="utf-8"
    )
    (change / "verification/gate.json").write_text(json.dumps({"approval": None}), encoding="utf-8")
    (change / "verification/qa.md").write_text("QA evidence\n", encoding="utf-8")
    (change / "verification/code-review.md").write_text("Review evidence\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=root, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.invalid"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"], cwd=root, check=True, capture_output=True
    )
    git_commit(root, "baseline")
    return root, change


def test_change_name_rejects_path_traversal(tmp_path: Path) -> None:
    root, _ = repo(tmp_path)
    try:
        module.change_dir(root, "../outside")
    except SystemExit as error:
        assert "invalid change name" in str(error)
    else:
        raise AssertionError("path traversal accepted")


def test_owner_decision_commit_does_not_self_invalidate_archive(
    tmp_path: Path, monkeypatch
) -> None:
    root, change = repo(tmp_path)
    monkeypatch.setattr(module, "gate", lambda *_: {"passed": True, "errors": [], "warnings": []})
    data = module.summary(root, "example")
    assert data["ready_for_human_review"] is True
    fingerprint = data["evidence_fingerprint"]

    module.write_decision(change, data, "ACCEPTED")
    assert module.fingerprint(root, change) == fingerprint
    git_commit(root, "decision only")

    assert module.fingerprint(root, change) == fingerprint
    assert module.archive_check(root, "example") == 0


@pytest.mark.parametrize(
    "relative_path",
    [
        "src/application.py",
        "services/api/src/ratsight_api/api/schemas.py",
        "tests/test_application.py",
        "openspec/changes/example/verification/qa.md",
    ],
)
def test_relevant_committed_changes_invalidate_fingerprint(
    tmp_path: Path, relative_path: str
) -> None:
    root, change = repo(tmp_path)
    before = module.fingerprint(root, change)
    path = root / relative_path
    contents = path.read_text(encoding="utf-8")
    path.write_text(contents + "# reviewed revision changed\n", encoding="utf-8")
    git_commit(root, f"change {relative_path}")
    assert module.fingerprint(root, change) != before


def test_missing_tasks_block_readiness(tmp_path: Path, monkeypatch) -> None:
    root, change = repo(tmp_path)
    (change / "tasks.md").unlink()
    monkeypatch.setattr(module, "gate", lambda *_: {"passed": True, "errors": [], "warnings": []})
    data = module.summary(root, "example")
    assert data["tasks"] == {"done": 0, "total": 0, "excluded_unfinished": 0}
    assert data["readiness"]["implementation_tasks_complete"] is False
    assert data["ready_for_human_review"] is False


@pytest.mark.parametrize("dirty_kind", ["staged", "unstaged", "untracked"])
def test_implementation_worktree_changes_block_clean_snapshot(
    tmp_path: Path, dirty_kind: str
) -> None:
    root, change = repo(tmp_path)
    if dirty_kind == "untracked":
        (root / "src/new_module.py").write_text("value = 2\n", encoding="utf-8")
    else:
        source = root / "src/application.py"
        source.write_text("value = 2\n", encoding="utf-8")
        if dirty_kind == "staged":
            subprocess.run(["git", "add", "src/application.py"], cwd=root, check=True)
    state = module.git_state(root, change)
    assert state["dirty"] is True
    assert module.summary(root, "example")["readiness"]["clean_implementation_snapshot"] is False


def test_owner_history_and_feedback_are_atomic_records(tmp_path: Path, monkeypatch) -> None:
    root, change = repo(tmp_path)
    monkeypatch.setattr(module, "gate", lambda *_: {"passed": True, "errors": [], "warnings": []})
    data = module.summary(root, "example")
    module.write_decision(change, data, "CHANGES_REQUESTED", "Please revise summary.")
    module.write_decision(change, data, "DEFERRED", "Later.")
    record = json.loads((change / module.OWNER_FILE).read_text(encoding="utf-8"))
    assert record["current"]["status"] == "DEFERRED"
    assert [item["status"] for item in record["history"]] == ["CHANGES_REQUESTED", "DEFERRED"]
    assert record["history"][0]["feedback"] == "Please revise summary."


def test_archive_check_rejects_stale_acceptance(tmp_path: Path, monkeypatch, capsys) -> None:
    root, change = repo(tmp_path)
    monkeypatch.setattr(module, "gate", lambda *_: {"passed": True, "errors": [], "warnings": []})
    data = module.summary(root, "example")
    module.write_decision(change, data, "ACCEPTED")
    git_commit(root, "record owner decision")
    source = root / "src/application.py"
    source.write_text(
        source.read_text(encoding="utf-8") + "# changed after acceptance\n", encoding="utf-8"
    )
    git_commit(root, "change implementation after acceptance")
    assert module.archive_check(root, "example") == 1
    assert "stale" in capsys.readouterr().err


def test_archive_check_rejects_missing_owner_acceptance(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root, _ = repo(tmp_path)
    monkeypatch.setattr(module, "gate", lambda *_: {"passed": True, "errors": [], "warnings": []})
    assert module.archive_check(root, "example") == 1
    assert "not ACCEPTED" in capsys.readouterr().err
