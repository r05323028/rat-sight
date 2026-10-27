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
    result = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=False)
    return result.stdout.strip() if result.returncode == 0 else ""


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
    return data


def fingerprint(directory: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(directory.rglob("*")):
        if not path.is_file() or path.relative_to(directory) == OWNER_FILE:
            continue
        digest.update(str(path.relative_to(directory)).encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def git_state(root: Path, directory: Path) -> dict[str, Any]:
    relative = str(directory.relative_to(root))
    status = git(root, "status", "--porcelain", "--", relative)
    owner_suffix = str(OWNER_FILE)
    lines = [line for line in status.splitlines() if not line[3:].endswith(owner_suffix)]
    return {"commit": git(root, "rev-parse", "HEAD"), "dirty": bool(lines), "status": lines}


def gate(root: Path, change: str) -> dict[str, Any]:
    result = subprocess.run(
        ["uv", "run", "python", "scripts/openspec_quality_gate.py", change, "--json"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
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


def task_counts(directory: Path) -> tuple[int, int]:
    path = directory / "tasks.md"
    if not path.is_file():
        return 0, 0
    text = path.read_text(encoding="utf-8")
    total = len(re.findall(r"^- \[[ xX]\]", text, re.MULTILINE))
    done = len(re.findall(r"^- \[[xX]\]", text, re.MULTILINE))
    return done, total


def summary(root: Path, change: str) -> dict[str, Any]:
    directory = change_dir(root, change)
    decision = load_decision(directory)
    current = decision.get("current")
    current = current if isinstance(current, dict) else None
    current_fingerprint = fingerprint(directory)
    stale = bool(
        current
        and current.get("status") == "ACCEPTED"
        and current.get("evidence_fingerprint") != current_fingerprint
    )
    state = git_state(root, directory)
    gate_result = gate(root, change)
    tasks_done, tasks_total = task_counts(directory)
    gate_file = directory / "verification" / "gate.json"
    gate_data: dict[str, Any] = {}
    if gate_file.is_file():
        try:
            parsed = json.loads(gate_file.read_text(encoding="utf-8"))
            gate_data = parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            pass
    approval = gate_data.get("approval")
    blockers = gate_result.get("errors", []) if isinstance(gate_result.get("errors"), list) else []
    return {
        "change": change,
        "proposal": proposal_summary(directory),
        "tasks": {"done": tasks_done, "total": tasks_total},
        "git": state,
        "gate": {
            "passed": gate_result.get("passed") is True,
            "errors": blockers,
            "warnings": gate_result.get("warnings", []),
        },
        "approval": approval if isinstance(approval, dict) else {"required": False},
        "owner_decision": current,
        "acceptance_stale": stale,
        "evidence_fingerprint": current_fingerprint,
        "ready_for_human_review": bool(gate_result.get("passed") is True and not blockers),
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
    print(f"  Quality Gate: {'PASS' if gate_data['passed'] else 'BLOCKED'}")
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
    os.replace(temporary, target)


def archive_check(root: Path, change: str) -> int:
    data = summary(root, change)
    owner = data["owner_decision"]
    if not data["gate"]["passed"]:
        print("archive blocked: quality gate did not pass", file=sys.stderr)
        return 1
    if not isinstance(owner, dict) or owner.get("status") != "ACCEPTED":
        print("archive blocked: current owner decision is not ACCEPTED", file=sys.stderr)
        return 1
    if data["acceptance_stale"]:
        print("archive blocked: owner acceptance is stale", file=sys.stderr)
        return 1
    print("archive eligible: current owner acceptance matches passing evidence")
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
