#!/usr/bin/env python3
"""Human-owned, local project-owner review and acceptance workflow."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.openspec_tasks import TaskCounts  # noqa: E402
from scripts.openspec_tasks import task_counts as count_tasks

CHANGE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
OWNER_FILE = Path("verification") / "owner-decision.json"
STATUSES = {"ACCEPTED", "CHANGES_REQUESTED", "DEFERRED"}


def repo_root(explicit: str | None = None) -> Path:
    if explicit:
        root = Path(explicit).resolve()
        if (root / "openspec").is_dir() and (root / "Makefile").is_file():
            return root
        raise SystemExit("--repo-root is not a RatSight repository")
    here = Path(__file__).resolve().parent
    for root in (here, *here.parents):
        if (root / "openspec").is_dir() and (root / "Makefile").is_file():
            return root
    raise SystemExit("could not locate repository root")


def change_dir(root: Path, change: str) -> Path:
    if not CHANGE_RE.fullmatch(change):
        raise SystemExit("invalid change name")
    path = (root / "openspec" / "changes" / change).resolve()
    if not path.is_relative_to((root / "openspec" / "changes").resolve()) or not path.is_dir():
        raise SystemExit(f"change does not exist: {change}")
    return path


def git(root: Path, *args: str) -> str:
    try:
        result = subprocess.run(
            ["git", *args], cwd=root, capture_output=True, text=True, check=False
        )
    except OSError:
        return ""
    return result.stdout.strip() if result.returncode == 0 else ""


def git_bytes(root: Path, *args: str) -> bytes | None:
    try:
        result = subprocess.run(["git", *args], cwd=root, capture_output=True, check=False)
    except OSError:
        return None
    return result.stdout if result.returncode == 0 else None


def now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_decision(directory: Path) -> dict[str, Any]:
    path = directory / OWNER_FILE
    if not path.is_file():
        return {"schema_version": 1, "change": directory.name, "current": None, "history": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"invalid owner decision file: {exc}") from exc
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise SystemExit("owner decision file has unsupported schema")
    if data.get("change") != directory.name:
        raise SystemExit("owner decision file change does not match its directory")
    current = data.get("current")
    history = data.get("history")
    if current is not None and not isinstance(current, dict):
        raise SystemExit("owner decision file has malformed current decision")
    if not isinstance(history, list) or any(not isinstance(item, dict) for item in history):
        raise SystemExit("owner decision file has malformed decision history")
    valid_statuses = {"ACCEPTED", "CHANGES_REQUESTED", "DEFERRED"}
    for item in ([current] if current is not None else []) + history:
        if item.get("status") not in valid_statuses:
            raise SystemExit("owner decision file has invalid decision status")
    return data


def fingerprint(root: Path, directory: Path) -> str | None:
    """Hash the committed repository content, excluding this change's owner decision.

    Git blob IDs bind every tracked path, mode, and content (including implementation,
    contracts, tests, migrations/configuration, OpenSpec artifacts, and verification).
    The commit ID is recorded separately; decision-only commits therefore do not create
    a fingerprint cycle. Uncommitted implementation is rejected by git_state.
    """
    commit = git(root, "rev-parse", "HEAD")
    entries = git_bytes(root, "ls-tree", "-r", "-z", "--full-tree", "HEAD")
    if not commit or entries is None:
        return None
    owner_path = os.fsencode((directory.relative_to(root) / OWNER_FILE).as_posix())
    digest = hashlib.sha256()
    for entry in entries.split(b"\0"):
        if not entry:
            continue
        _metadata, separator, path = entry.partition(b"\t")
        if not separator:
            return None
        if path == owner_path:
            continue
        digest.update(entry)
        digest.update(b"\0")
    return digest.hexdigest()


def git_state(root: Path, directory: Path) -> dict[str, Any]:
    commit = git(root, "rev-parse", "HEAD")
    top_level = git(root, "rev-parse", "--show-toplevel")
    raw_status = git_bytes(root, "status", "--porcelain=v1", "-z", "--untracked-files=all")
    if (
        not commit
        or not top_level
        or Path(top_level).resolve() != root.resolve()
        or raw_status is None
    ):
        return {
            "commit": commit,
            "dirty": True,
            "status": ["Git repository or committed HEAD unavailable"],
            "valid": False,
        }
    owner_path = os.fsencode((directory.relative_to(root) / OWNER_FILE).as_posix())
    records = raw_status.split(b"\0")
    lines: list[str] = []
    index = 0
    while index < len(records):
        record = records[index]
        index += 1
        if not record:
            continue
        code, separator, path = record.partition(b" ")
        if not separator:
            lines.append(os.fsdecode(record))
            continue
        paths = [path]
        if b"R" in code or b"C" in code:
            if index < len(records) and records[index]:
                paths.append(records[index])
                index += 1
        if paths == [owner_path]:
            continue
        lines.append(f"{code.decode('ascii', errors='replace')} {os.fsdecode(paths[0])}")
    return {"commit": commit, "dirty": bool(lines), "status": lines, "valid": True}


def gate(root: Path, change: str) -> dict[str, Any]:
    try:
        result = subprocess.run(
            ["uv", "run", "python", "scripts/openspec_quality_gate.py", change, "--json"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        return {"passed": False, "errors": [{"message": str(exc)}]}
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"passed": False, "errors": [{"message": (result.stdout + result.stderr)[-1000:]}]}
    return (
        payload
        if isinstance(payload, dict)
        else {"passed": False, "errors": [{"message": "invalid gate output"}]}
    )


def proposal_summary(directory: Path) -> str:
    path = directory / "proposal.md"
    if not path.is_file():
        return "missing proposal.md"
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("#"):
            continue
        if line.strip():
            return line.strip()
    return "no proposal summary"


def evidence_present(path: Path) -> bool:
    try:
        return path.is_file() and bool(path.read_text(encoding="utf-8").strip())
    except (OSError, UnicodeError):
        return False


def task_counts(directory: Path) -> TaskCounts:
    path = directory / "tasks.md"
    if not path.is_file():
        return TaskCounts()
    try:
        return count_tasks(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError):
        return TaskCounts()


def summary(root: Path, change: str) -> dict[str, Any]:
    directory = change_dir(root, change)
    decision = load_decision(directory)
    current = decision.get("current")
    current = current if isinstance(current, dict) else None
    state = git_state(root, directory)
    current_fingerprint = fingerprint(root, directory)
    stale = bool(
        current
        and current.get("status") == "ACCEPTED"
        and (
            current_fingerprint is None
            or current.get("evidence_fingerprint") != current_fingerprint
            or state["dirty"]
            or not state["valid"]
        )
    )
    gate_result = gate(root, change)
    counts = task_counts(directory)
    tasks_file = directory / "tasks.md"
    gate_file = directory / "verification" / "gate.json"
    gate_data: dict[str, Any] = {}
    if gate_file.is_file():
        try:
            parsed = json.loads(gate_file.read_text(encoding="utf-8"))
            gate_data = parsed if isinstance(parsed, dict) else {}
        except (OSError, json.JSONDecodeError) as exc:
            gate_data = {"_invalid_record": str(exc)}
    approval = gate_data.get("approval")
    approval = approval if isinstance(approval, dict) else {"required": False}
    blockers = gate_result.get("errors", []) if isinstance(gate_result.get("errors"), list) else []
    gate_passed = gate_result.get("passed") is True and not blockers
    required_evidence = (
        directory / "verification" / "qa.md",
        directory / "verification" / "code-review.md",
    )
    verification_complete = all(evidence_present(path) for path in required_evidence)
    implementation_complete = tasks_file.is_file() and counts.complete
    approval_satisfied = not approval.get("required") or approval.get("decision") == "APPROVED"
    clean_snapshot = state["valid"] and not state["dirty"] and current_fingerprint is not None
    readiness = {
        "implementation_tasks_complete": implementation_complete,
        "verification_evidence_complete": verification_complete,
        "quality_gate_passed": gate_passed,
        "required_policy_approvals_satisfied": approval_satisfied,
        "clean_implementation_snapshot": clean_snapshot,
        "owner_acceptance_pending": not (
            current and current.get("status") == "ACCEPTED" and not stale
        ),
    }
    ready = all(
        readiness[key]
        for key in (
            "implementation_tasks_complete",
            "verification_evidence_complete",
            "quality_gate_passed",
            "required_policy_approvals_satisfied",
            "clean_implementation_snapshot",
        )
    )
    return {
        "change": change,
        "proposal": proposal_summary(directory),
        "tasks": {
            "done": counts.done,
            "total": counts.total,
            "excluded_unfinished": counts.excluded_unfinished,
        },
        "git": state,
        "gate": {
            "passed": gate_passed,
            "errors": blockers,
            "warnings": gate_result.get("warnings", []),
        },
        "approval": approval,
        "owner_decision": current,
        "acceptance_stale": stale,
        "evidence_fingerprint": current_fingerprint,
        "readiness": readiness,
        "ready_for_human_review": ready,
        "known_limitations": [
            item.get("message", "")
            for item in gate_result.get("warnings", [])
            if isinstance(item, dict)
        ],
    }


def print_summary(data: dict[str, Any]) -> None:
    tasks = data["tasks"]
    gate_data = data["gate"]
    approval = data["approval"]
    owner = data["owner_decision"]
    status = owner.get("status") if isinstance(owner, dict) else None
    if data["acceptance_stale"]:
        status = f"{status} (STALE)"
    print("RatSight — Change Review\n")
    print(f"Change: {data['change']}")
    print(f"  Proposal: {data['proposal']}")
    print(f"  Tasks: {tasks['done']} / {tasks['total']} completed")
    commit = data["git"]["commit"] or "unavailable"
    cleanliness = "dirty" if data["git"]["dirty"] else "clean"
    print(f"  Git: {commit} ({cleanliness})")
    readiness = data["readiness"]
    task_state = "COMPLETE" if readiness["implementation_tasks_complete"] else "INCOMPLETE"
    evidence_state = "COMPLETE" if readiness["verification_evidence_complete"] else "INCOMPLETE"
    print(f"  Implementation Tasks: {task_state}")
    print(f"  Verification Evidence: {evidence_state}")
    print(f"  Quality Gate: {'PASS' if gate_data['passed'] else 'BLOCKED'}")
    snapshot_state = "YES" if readiness["clean_implementation_snapshot"] else "NO"
    print(f"  Clean Implementation Snapshot: {snapshot_state}")
    approval_required = "YES" if approval.get("required") else "NO"
    approval_state = approval.get("decision", "not required")
    print(f"  Required Policy Approval: {approval_required} ({approval_state})")
    print(f"  Project Owner Acceptance: {status or 'PENDING'}")
    ready = "YES" if data["ready_for_human_review"] else "NO"
    print(f"  Ready for Human Review: {ready}")
    if gate_data["errors"]:
        print("\nBlocking findings:")
        for item in gate_data["errors"]:
            print(f"  - {item.get('code', 'error')}: {item.get('message', '')}")
    if data["known_limitations"]:
        print("\nKnown limitations:")
        for item in data["known_limitations"]:
            print(f"  - {item}")
    print(f"\nEvidence fingerprint: {data['evidence_fingerprint']}")


def write_decision(directory: Path, data: dict[str, Any], status: str, feedback: str = "") -> None:
    if status not in {"ACCEPTED", "CHANGES_REQUESTED", "DEFERRED"}:
        raise ValueError(f"unsupported owner decision: {status}")
    if status == "ACCEPTED" and not data.get("ready_for_human_review"):
        raise SystemExit("acceptance blocked: implementation readiness requirements are incomplete")
    record = load_decision(directory)
    entry = {
        "status": status,
        "reviewed_commit": data["git"]["commit"],
        "evidence_fingerprint": data["evidence_fingerprint"],
        "decided_at": now(),
        "decision_source": "local_interactive_cli",
        "working_tree_dirty": data["git"]["dirty"],
    }
    if feedback:
        entry["feedback"] = feedback
    history_value = record.get("history")
    history = list(history_value) if isinstance(history_value, list) else []
    history.append(entry)
    output = {
        "schema_version": 1,
        "change": data["change"],
        "current": entry,
        "history": history,
    }
    target = directory / OWNER_FILE
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=target.parent, delete=False
    ) as handle:
        json.dump(output, handle, indent=2)
        handle.write("\n")
        temporary = Path(handle.name)
    try:
        os.replace(temporary, target)
    except OSError:
        temporary.unlink(missing_ok=True)
        raise


def archive_check(root: Path, change: str) -> int:
    data = summary(root, change)
    owner = data["owner_decision"]
    readiness = data["readiness"]
    if data["acceptance_stale"]:
        print("archive blocked: owner acceptance is stale", file=sys.stderr)
        return 1
    if not readiness["implementation_tasks_complete"]:
        print(
            "archive blocked: required implementation tasks are incomplete or missing",
            file=sys.stderr,
        )
        return 1
    if not readiness["verification_evidence_complete"]:
        print("archive blocked: required verification evidence is incomplete", file=sys.stderr)
        return 1
    if not readiness["quality_gate_passed"]:
        print("archive blocked: quality gate did not pass", file=sys.stderr)
        return 1
    if not readiness["required_policy_approvals_satisfied"]:
        print("archive blocked: mandatory policy approval is not APPROVED", file=sys.stderr)
        return 1
    if not readiness["clean_implementation_snapshot"]:
        print("archive blocked: implementation snapshot is dirty or unavailable", file=sys.stderr)
        return 1
    if not isinstance(owner, dict) or owner.get("status") != "ACCEPTED":
        status = owner.get("status") if isinstance(owner, dict) else None
        if status == "CHANGES_REQUESTED":
            print("archive blocked: owner requested changes", file=sys.stderr)
        elif status == "DEFERRED":
            print("archive blocked: owner decision is deferred", file=sys.stderr)
        else:
            print("archive blocked: current owner decision is not ACCEPTED", file=sys.stderr)
        return 1
    print("archive eligible: current owner acceptance matches the clean snapshot")
    return 0


def decide(root: Path, change: str) -> int:
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        print(
            "change-accept requires an interactive terminal; no decision written", file=sys.stderr
        )
        return 2
    data = summary(root, change)
    print_summary(data)
    print("\nProject Owner Decision\n1. Accept\n2. Request Changes\n3. Defer\n4. Cancel")
    choice = input("Choose 1-4: ").strip()
    if choice == "4":
        print("Cancelled; no decision written.")
        return 0
    if choice == "1":
        if not data["ready_for_human_review"] or data["acceptance_stale"]:
            print(
                "Acceptance blocked: gate/readiness, clean state, or stale decision failed.",
                file=sys.stderr,
            )
            return 1
        if data["approval"].get("required") and data["approval"].get("decision") != "APPROVED":
            print("Acceptance blocked: mandatory policy approval is not APPROVED.", file=sys.stderr)
            return 1
        confirmation = input(f"Type ACCEPT {change} to confirm: ").strip()
        if confirmation != f"ACCEPT {change}":
            print("Confirmation did not match; no decision written.")
            return 1
        write_decision(change_dir(root, change), data, "ACCEPTED")
        print("Recorded ACCEPTED. Archive remains a separate explicit action.")
        return 0
    if choice == "2":
        feedback = input("Feedback (required): ").strip()
        if not feedback:
            print("Feedback is required; no decision written.", file=sys.stderr)
            return 1
        write_decision(change_dir(root, change), data, "CHANGES_REQUESTED", feedback)
        print("Recorded CHANGES_REQUESTED.")
        return 0
    if choice == "3":
        write_decision(
            change_dir(root, change), data, "DEFERRED", input("Reason (optional): ").strip()
        )
        print("Recorded DEFERRED.")
        return 0
    print("Invalid choice; no decision written.", file=sys.stderr)
    return 2


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Review and record human-owned OpenSpec acceptance."
    )
    parser.add_argument("command", choices=["review", "status", "decide", "archive-check"])
    parser.add_argument("change")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--repo-root")
    args = parser.parse_args()
    root = repo_root(args.repo_root)
    data = summary(root, args.change)
    if args.command == "decide":
        return decide(root, args.change)
    if args.command == "archive-check":
        return archive_check(root, args.change)
    if args.json or args.command == "status":
        print(json.dumps(data, indent=2))
    else:
        print_summary(data)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
