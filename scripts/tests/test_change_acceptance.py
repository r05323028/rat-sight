from __future__ import annotations

import importlib.util
import json
from pathlib import Path

SCRIPT = Path(__file__).parents[1] / "change_acceptance.py"
spec = importlib.util.spec_from_file_location("change_acceptance", SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def repo(tmp_path: Path) -> tuple[Path, Path]:
    root = tmp_path / "repo"
    change = root / "openspec/changes/example"
    (change / "verification").mkdir(parents=True)
    (root / "Makefile").write_text("", encoding="utf-8")
    (root / "openspec/config.yaml").write_text("", encoding="utf-8")
    (change / "proposal.md").write_text("# Example\n\nSmall workflow change.\n", encoding="utf-8")
    (change / "tasks.md").write_text("- [x] done\n- [ ] later\n", encoding="utf-8")
    (change / "verification/gate.json").write_text(json.dumps({"approval": None}), encoding="utf-8")
    return root, change


def test_change_name_rejects_path_traversal(tmp_path: Path) -> None:
    root, _ = repo(tmp_path)
    try:
        module.change_dir(root, "../outside")
    except SystemExit as error:
        assert "invalid change name" in str(error)
    else:
        raise AssertionError("path traversal accepted")


def test_fingerprint_excludes_owner_decision(tmp_path: Path) -> None:
    _, change = repo(tmp_path)
    before = module.fingerprint(change)
    decision = change / "verification/owner-decision.json"
    decision.write_text('{"status":"DEFERRED"}\n', encoding="utf-8")
    assert module.fingerprint(change) == before


def test_owner_history_and_feedback_are_atomic_records(tmp_path: Path, monkeypatch) -> None:
    root, change = repo(tmp_path)
    monkeypatch.setattr(module, "gate", lambda *_: {"passed": True, "errors": [], "warnings": []})
    monkeypatch.setattr(module, "git", lambda _root, *args: "commit" if "rev-parse" in args else "")
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
    monkeypatch.setattr(module, "git", lambda _root, *args: "commit" if "rev-parse" in args else "")
    data = module.summary(root, "example")
    module.write_decision(change, data, "ACCEPTED")
    (change / "proposal.md").write_text("changed\n", encoding="utf-8")
    assert module.archive_check(root, "example") == 1
    assert "stale" in capsys.readouterr().err


def test_archive_check_rejects_missing_owner_acceptance(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root, _ = repo(tmp_path)
    monkeypatch.setattr(module, "gate", lambda *_: {"passed": True, "errors": [], "warnings": []})
    monkeypatch.setattr(module, "git", lambda _root, *args: "commit" if "rev-parse" in args else "")
    assert module.archive_check(root, "example") == 1
    assert "not ACCEPTED" in capsys.readouterr().err
