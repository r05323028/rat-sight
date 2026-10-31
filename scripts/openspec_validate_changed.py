#!/usr/bin/env python3
"""Validate the OpenSpec changes touched by a commit range.

This is the CI-side structural check. It runs `openspec schema validate` once and
`openspec validate <change>` for each touched change. It does not run tests, the
quality gate, or any semantic review, so a pass means the artifacts parse and are
structurally valid, nothing more.

The range base is resolved explicitly and must name a real commit other than
HEAD. A shallow checkout, a missing base branch, or a failed diff is an error,
not an empty change list: validating nothing is never reported as success.

Usage:
    python scripts/openspec_validate_changed.py            # base from CI env or origin/main
    python scripts/openspec_validate_changed.py --all      # every active change
    python scripts/openspec_validate_changed.py --base origin/main
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

CHANGES = Path("openspec") / "changes"
ARCHIVE = "archive"
SCHEMA_NAME = "evidence-driven"
ZERO_SHA = re.compile(r"^0+$")


def find_repo(start: Path) -> Path | None:
    for candidate in (start.resolve(), *start.resolve().parents):
        if (candidate / "openspec").is_dir():
            return candidate
    return None


def find_openspec() -> str | None:
    return os.environ.get("RATSIGHT_OPENSPEC_BIN") or shutil.which("openspec")


def git(repo: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", *args], cwd=repo, capture_output=True, text=True, check=False, timeout=120
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return result.stdout if result.returncode == 0 else None


def git_commit(repo: Path, ref: str) -> str | None:
    output = git(repo, "rev-parse", "--verify", "--quiet", ref + "^{commit}")
    commit = output.strip() if output is not None else ""
    return commit or None


def change_names_from_paths(paths: list[str]) -> list[str]:
    """Return change directory names referenced by repository-relative paths."""
    names: set[str] = set()
    prefix = CHANGES.as_posix() + "/"
    for path in paths:
        if not path.startswith(prefix):
            continue
        remainder = path[len(prefix) :]
        if not remainder or "/" not in remainder:
            continue
        name = remainder.split("/", 1)[0]
        if name and name != ARCHIVE and not name.startswith("."):
            names.add(name)
    return sorted(names)


def active_changes(repo: Path) -> list[str]:
    directory = repo / CHANGES
    if not directory.is_dir():
        return []
    return sorted(
        item.name
        for item in directory.iterdir()
        if item.is_dir() and item.name != ARCHIVE and not item.name.startswith(".")
    )


def base_candidates(explicit: str | None) -> tuple[list[str], str]:
    """Return base ref candidates, in priority order, and how they were chosen."""
    if explicit:
        return [explicit], "argument"
    event = os.environ.get("GITHUB_EVENT_NAME", "")
    if event.startswith("pull_request"):
        base_ref = os.environ.get("GITHUB_BASE_REF", "")
        if not base_ref:
            return [], "pull request event without GITHUB_BASE_REF"
        return ["origin/" + base_ref], "pull request base"
    before = os.environ.get("GITHUB_EVENT_BEFORE", "")
    if before and not ZERO_SHA.match(before):
        return [before], "push event before"
    return ["origin/main", "main"], "default branch"


def resolve_base(repo: Path, explicit: str | None) -> tuple[tuple[str, str, str] | None, str]:
    """Return ((ref, commit, source), "") or (None, reason)."""
    candidates, source = base_candidates(explicit)
    if not candidates:
        return None, source
    for ref in candidates:
        commit = git_commit(repo, ref)
        if commit is not None:
            return (ref, commit, source), ""
    tried = ", ".join(candidates)
    return None, (
        "range base "
        + tried
        + " ("
        + source
        + ") does not resolve; a shallow checkout hides the base commit. Fetch full"
        " history (actions/checkout with fetch-depth: 0) or pass --base explicitly"
    )


def changed_names(repo: Path, base_commit: str) -> tuple[list[str] | None, str | None]:
    """Return the touched change names for base...HEAD, or why the range is unusable."""
    head = git_commit(repo, "HEAD")
    if head is None:
        return None, "HEAD does not resolve to a commit; the range cannot be evaluated"
    if head == base_commit:
        return None, (
            "range base resolves to HEAD, so the diff is empty: this is the shallow-checkout"
            " or missing-fetch case, not a clean change set. Fetch the base commit"
            " (fetch-depth: 0) or pass the pre-push commit or pull-request base"
        )
    output = git(
        repo,
        "diff",
        "--name-only",
        "--diff-filter=d",
        base_commit + "..." + head,
        "--",
        CHANGES.as_posix(),
    )
    if output is None:
        return None, "git diff failed for " + base_commit + "..." + head
    return change_names_from_paths([line for line in output.splitlines() if line.strip()]), None


def validate(repo: Path, names: list[str], binary: str) -> tuple[list[str], list[dict[str, str]]]:
    failures: list[dict[str, str]] = []
    checks: list[str] = []
    schema = subprocess.run(
        [binary, "schema", "validate", SCHEMA_NAME],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    checks.append("schema " + SCHEMA_NAME)
    if schema.returncode != 0:
        output = (schema.stdout + schema.stderr).strip()
        failures.append({"target": "schema " + SCHEMA_NAME, "message": output[-1000:]})
    for name in names:
        result = subprocess.run(
            [binary, "validate", name],
            cwd=repo,
            capture_output=True,
            text=True,
            check=False,
            timeout=120,
        )
        checks.append("change " + name)
        if result.returncode != 0:
            output = (result.stdout + result.stderr).strip()
            failures.append({"target": name, "message": output[-1000:]})
    return checks, failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate OpenSpec changes touched by a commit range."
    )
    parser.add_argument("--repo-root", help="repository root; default: nearest openspec/ directory")
    parser.add_argument(
        "--base", help="git ref to diff against; default: CI event base or origin/main"
    )
    parser.add_argument("--all", action="store_true", help="validate every active change")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    args = parser.parse_args(argv)

    repo = Path(args.repo_root).resolve() if args.repo_root else find_repo(Path.cwd())
    if repo is None:
        print("openspec validate: no openspec/ directory found", file=sys.stderr)
        return 2

    base_ref: str | None = None
    base_source = "all active changes" if args.all else ""
    if args.all:
        names: list[str] | None = active_changes(repo)
        error: str | None = None
    else:
        resolved, reason = resolve_base(repo, args.base)
        if resolved is None:
            print("openspec validate: " + reason, file=sys.stderr)
            if args.json:
                print(
                    json.dumps(
                        {
                            "base": None,
                            "base_source": reason,
                            "changes": None,
                            "evaluated": 0,
                            "failed": True,
                        },
                        indent=2,
                    )
                )
            return 2
        base_ref, base_commit, base_source = resolved
        names, error = changed_names(repo, base_commit)
        if names is None:
            print("openspec validate: " + (error or "range cannot be evaluated"), file=sys.stderr)
            if args.json:
                print(
                    json.dumps(
                        {
                            "base": base_ref,
                            "base_commit": base_commit,
                            "base_source": base_source,
                            "changes": None,
                            "evaluated": 0,
                            "failed": True,
                        },
                        indent=2,
                    )
                )
            return 2

    names = names or []
    note = ""
    if not args.all and not names:
        note = "range contains no OpenSpec change paths; schema validation still runs"

    binary = find_openspec()
    if not binary:
        print("openspec validate: OpenSpec CLI is required", file=sys.stderr)
        return 2

    checks, failures = validate(repo, names, binary)
    payload = {
        "base": base_ref,
        "base_source": base_source,
        "changes": names,
        "evaluated": len(names),
        "checks": checks,
        "failures": failures,
        "note": note,
        "limitation": "structural validation only; it does not run tests or the quality gate",
    }
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        if note:
            print("note: " + note)
        summary = ", ".join(checks) if checks else "nothing to validate"
        print(
            "validated "
            + str(len(names))
            + " change(s) against "
            + str(base_ref or "all active changes")
            + ": "
            + summary
        )
        for failure in failures:
            print("FAIL " + failure["target"] + ": " + failure["message"], file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
