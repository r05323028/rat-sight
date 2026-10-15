#!/usr/bin/env python3
"""Deterministic gate for recorded review, traceability, verification, and approval state.

OpenSpec owns schema, artifact dependencies, change validation, status, and delta
requirements. This script checks the small machine-readable state in
verification/gate.json plus the required narrative review records.

The gate can check that claims are present and internally consistent. It cannot
prove that reviews occurred independently, commands ran, approval was human, or
scientific conclusions are valid. See guidance/openspec-workflow.md.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, TypeGuard

EXIT_PASS = 0
EXIT_BLOCKED = 1
EXIT_USAGE = 2
SCHEMA_NAME = "evidence-driven"
CHANGES = Path("openspec") / "changes"
GATE_RECORD = Path("verification") / "gate.json"
EVIDENCE_DIR = Path("docs") / "evidence"
DECISIONS = {"PASS", "PASS_WITH_WARNINGS", "BLOCKED"}
SEVERITIES = {"BLOCKING", "MAJOR", "MINOR", "INFO"}
FINDING_STATES = {"OPEN", "RESOLVED", "ACCEPTED_RISK", "DEFERRED"}
TRACE_STATES = {"VERIFIED", "PARTIALLY_VERIFIED", "UNVERIFIED", "NOT_APPLICABLE"}
DATA_CLASSES = {"OBSERVED", "INFERRED", "SIMULATED", "UNVERIFIED"}
APPROVAL_TRIGGERS = {
    "ARCHITECTURE_CHANGE",
    "NEW_SCIENTIFIC_ASSUMPTION",
    "UNKNOWN_PARAMETER_DEFAULT",
    "SENSITIVE_DATA_POLICY",
    "SECURITY_OR_POLICY_CHANGE",
    "ACCEPTANCE_EXCEPTION",
}


def issue(report: dict[str, Any], code: str, path: Path, message: str) -> None:
    report["errors"].append({"code": code, "path": str(path), "message": message})


def warn(report: dict[str, Any], code: str, path: Path, message: str) -> None:
    report["warnings"].append({"code": code, "path": str(path), "message": message})


def check(report: dict[str, Any], name: str, ok: bool, detail: str) -> None:
    report["checks"].append({"name": name, "status": "ok" if ok else "fail", "detail": detail})


def text(value: Any) -> TypeGuard[str]:
    return isinstance(value, str) and bool(value.strip())


def repo_file_exists(repo: Path, value: Any) -> bool:
    if not text(value):
        return False
    candidate = Path(value)
    if candidate.is_absolute():
        return False
    try:
        root = repo.resolve()
        resolved = (repo / candidate).resolve()
        return resolved.is_relative_to(root) and resolved.is_file()
    except (OSError, RuntimeError):
        return False


def nonempty_file(path: Path) -> bool:
    try:
        return path.is_file() and bool(path.read_text(encoding="utf-8").strip())
    except (OSError, UnicodeError):
        return False


def active_changes(repo: Path) -> list[str]:
    directory = repo / CHANGES
    if not directory.is_dir():
        return []
    return sorted(
        item.name
        for item in directory.iterdir()
        if item.is_dir() and item.name != "archive" and not item.name.startswith(".")
    )


def find_repo(start: Path) -> Path | None:
    for candidate in (start.resolve(), *start.resolve().parents):
        if (candidate / "openspec").is_dir():
            return candidate
    return None


def find_openspec() -> str | None:
    return os.environ.get("RATSIGHT_OPENSPEC_BIN") or shutil.which("openspec")


def run_cli(binary: str, args: list[str], repo: Path) -> subprocess.CompletedProcess[str] | None:
    try:
        return subprocess.run(
            [binary, *args],
            cwd=repo,
            capture_output=True,
            text=True,
            timeout=180,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None


def cli_json(
    report: dict[str, Any],
    binary: str,
    args: list[str],
    repo: Path,
    label: str,
) -> dict[str, Any] | None:
    result = run_cli(binary, args, repo)
    path = repo / CHANGES
    if result is None:
        issue(report, "GATE-OPENSPEC", path, "could not run openspec " + " ".join(args))
        return None
    if result.returncode != 0:
        output = (result.stdout + result.stderr).strip().splitlines()
        issue(
            report,
            "GATE-OPENSPEC",
            path,
            "openspec " + " ".join(args) + " failed: " + (output[-1] if output else "no output"),
        )
        return None
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        issue(report, "GATE-OPENSPEC-JSON", path, label + " did not return valid JSON")
        return None
    if not isinstance(payload, dict):
        issue(report, "GATE-OPENSPEC-JSON", path, label + " returned an unexpected JSON value")
        return None
    return payload


def requirement_ids(report: dict[str, Any], payload: dict[str, Any]) -> set[str] | None:
    deltas = payload.get("deltas")
    if not isinstance(deltas, list):
        issue(report, "GATE-OPENSPEC-DELTA", CHANGES, "OpenSpec delta output has no deltas list")
        return None
    found: set[str] = set()
    for delta in deltas:
        if not isinstance(delta, dict) or not text(delta.get("spec")):
            issue(
                report,
                "GATE-OPENSPEC-DELTA",
                CHANGES,
                "OpenSpec returned a delta without a spec name",
            )
            continue
        requirements = delta.get("requirements")
        if not isinstance(requirements, list):
            single = delta.get("requirement")
            requirements = [single] if isinstance(single, dict) else []
        for requirement in requirements:
            if not isinstance(requirement, dict) or not text(requirement.get("name")):
                issue(
                    report,
                    "GATE-OPENSPEC-DELTA",
                    CHANGES,
                    "OpenSpec returned a requirement without a name",
                )
                continue
            identifier = str(delta["spec"]) + "#" + str(requirement["name"])
            if identifier in found:
                issue(
                    report,
                    "GATE-OPENSPEC-DELTA",
                    CHANGES,
                    "duplicate OpenSpec requirement: " + identifier,
                )
            found.add(identifier)
    return found


def check_openspec(
    report: dict[str, Any], repo: Path, change: str, skipped: bool
) -> set[str] | None:
    if skipped:
        warn(
            report,
            "GATE-OPENSPEC-SKIPPED",
            repo / "openspec",
            "--skip-openspec skips schema/change, artifact-status, and requirement-coverage checks",
        )
        check(report, "OpenSpec CLI", True, "explicitly skipped; limitations recorded")
        return None
    binary = find_openspec()
    if not binary:
        issue(report, "GATE-OPENSPEC-MISSING", repo / "openspec", "openspec CLI is required")
        check(report, "OpenSpec CLI", False, "CLI unavailable")
        return None

    start = len(report["errors"])
    for args in (
        ["schema", "validate", SCHEMA_NAME],
        ["validate", change],
    ):
        result = run_cli(binary, args, repo)
        if result is None or result.returncode != 0:
            output = (
                "could not run command"
                if result is None
                else (result.stdout + result.stderr).strip()
            )
            issue(
                report,
                "GATE-OPENSPEC",
                repo / CHANGES / change,
                "openspec " + " ".join(args) + " failed: " + output[-1000:],
            )

    status = cli_json(report, binary, ["status", "--change", change, "--json"], repo, "status")
    if status is not None:
        if status.get("schemaName") != SCHEMA_NAME:
            issue(
                report,
                "GATE-OPENSPEC-SCHEMA",
                repo / CHANGES / change,
                "change does not use schema " + SCHEMA_NAME,
            )
        artifacts = status.get("artifactPaths")
        if not isinstance(artifacts, dict) or "adversarial-review" not in artifacts:
            issue(
                report,
                "GATE-OPENSPEC-ARTIFACT",
                repo / CHANGES / change,
                "OpenSpec status does not recognize adversarial-review",
            )
        if status.get("isPlanningComplete") is not True:
            issue(
                report,
                "GATE-OPENSPEC-STATUS",
                repo / CHANGES / change,
                "OpenSpec reports planning artifacts incomplete",
            )

    deltas = cli_json(
        report, binary, ["show", change, "--json", "--deltas-only"], repo, "delta output"
    )
    expected = requirement_ids(report, deltas) if deltas is not None else None
    check(
        report,
        "OpenSpec CLI",
        len(report["errors"]) == start,
        "schema, change, status, and delta checks",
    )
    return expected


def load_gate_record(report: dict[str, Any], change_dir: Path) -> dict[str, Any] | None:
    path = change_dir / GATE_RECORD
    if not path.is_file():
        issue(report, "GATE-RECORD-MISSING", path, "verification/gate.json is required")
        check(report, "gate state", False, "record missing")
        return None
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        issue(report, "GATE-RECORD-JSON", path, "cannot read gate record: " + str(error))
        check(report, "gate state", False, "invalid JSON")
        return None
    if not isinstance(record, dict):
        issue(report, "GATE-RECORD-JSON", path, "gate record must be a JSON object")
        check(report, "gate state", False, "not an object")
        return None
    check(report, "gate state", True, "JSON loaded")
    return record


def check_verification(
    report: dict[str, Any], change_dir: Path, record: dict[str, Any]
) -> dict[str, dict[str, Any]]:
    errors_before = len(report["errors"])
    path = change_dir / GATE_RECORD
    entries = record.get("verification")
    if not isinstance(entries, list) or not entries:
        issue(report, "GATE-VERIFICATION-MISSING", path, "record at least one verification run")
        check(report, "verification evidence", False, "no verification runs")
        return {}
    indexed: dict[str, dict[str, Any]] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            issue(report, "GATE-VERIFICATION-ENTRY", path, "verification entries must be objects")
            continue
        identifier = entry.get("id")
        if not text(identifier):
            issue(report, "GATE-VERIFICATION-ID", path, "verification entry has no id")
            continue
        if identifier in indexed:
            issue(report, "GATE-VERIFICATION-ID", path, "duplicate verification id: " + identifier)
            continue
        indexed[identifier] = entry
        for key in ("command", "result", "reference"):
            if not text(entry.get(key)):
                issue(report, "GATE-VERIFICATION-ENTRY", path, identifier + " has no " + key)
        code = entry.get("exit_code")
        if type(code) is not int:
            issue(report, "GATE-VERIFICATION-EXIT", path, identifier + " has no integer exit_code")
        elif code != 0:
            issue(
                report,
                "GATE-VERIFICATION-FAILED",
                path,
                identifier + " records exit code " + str(code),
            )
    check(
        report,
        "verification evidence",
        len(report["errors"]) == errors_before,
        str(len(indexed)) + " recorded run(s)",
    )
    return indexed


def check_review(
    report: dict[str, Any],
    change_dir: Path,
    reviews: Any,
    key: str,
    report_path: str,
    code: str,
) -> tuple[set[str], list[str]]:
    errors_before = len(report["errors"])
    path = change_dir / report_path
    if not nonempty_file(path):
        issue(report, code + "-MISSING", path, "mandatory review report is missing or empty")
    review = reviews.get(key) if isinstance(reviews, dict) else None
    if not isinstance(review, dict):
        issue(
            report,
            code + "-STATE",
            change_dir / GATE_RECORD,
            "gate.json has no " + key + " review state",
        )
        check(report, key + " review", False, "state missing")
        return set(), []

    decision = review.get("decision")
    if not text(decision) or decision not in DECISIONS:
        issue(
            report,
            code + "-DECISION",
            change_dir / GATE_RECORD,
            "review decision must be PASS, PASS_WITH_WARNINGS, or BLOCKED",
        )
    elif decision == "BLOCKED":
        issue(report, code + "-BLOCKED", change_dir / GATE_RECORD, "review decision is BLOCKED")

    findings = review.get("findings")
    accepted: list[str] = []
    identifiers: set[str] = set()
    unresolved = False
    if not isinstance(findings, list):
        issue(report, code + "-FINDINGS", change_dir / GATE_RECORD, "findings must be a list")
        findings = []
    for finding in findings:
        if not isinstance(finding, dict):
            issue(report, code + "-FINDING", change_dir / GATE_RECORD, "findings must be objects")
            continue
        identifier = finding.get("id")
        severity = finding.get("severity")
        state = finding.get("status")
        if not text(identifier) or identifier in identifiers:
            issue(
                report,
                code + "-FINDING-ID",
                change_dir / GATE_RECORD,
                "finding ids must be non-empty and unique within each review",
            )
            continue
        identifiers.add(identifier)
        if not text(severity) or severity not in SEVERITIES:
            issue(
                report,
                code + "-FINDING",
                change_dir / GATE_RECORD,
                identifier + " has an unknown severity",
            )
        if not text(state) or state not in FINDING_STATES:
            issue(
                report,
                code + "-FINDING",
                change_dir / GATE_RECORD,
                identifier + " has an unknown status",
            )
            continue
        if state != "RESOLVED":
            unresolved = True
        if severity == "BLOCKING" and state != "RESOLVED":
            issue(
                report,
                code + "-BLOCKING",
                change_dir / GATE_RECORD,
                identifier
                + " is a blocking finding not marked RESOLVED; blocking risks are not waivable",
            )
        elif state == "ACCEPTED_RISK":
            accepted.append(identifier)
            if not text(finding.get("residual_risk")):
                issue(
                    report,
                    code + "-RISK",
                    change_dir / GATE_RECORD,
                    identifier + " must preserve residual risk",
                )
    if unresolved and decision == "PASS":
        issue(
            report,
            code + "-DECISION-CONSISTENCY",
            change_dir / GATE_RECORD,
            "unresolved findings require PASS_WITH_WARNINGS or BLOCKED",
        )
    check(
        report,
        key + " review",
        len(report["errors"]) == errors_before,
        str(len(identifiers)) + " finding(s), decision " + str(decision),
    )
    return identifiers, accepted


def check_paths(
    report: dict[str, Any], repo: Path, path: Path, values: Any, label: str
) -> list[str]:
    if not isinstance(values, list) or not values:
        issue(
            report, "GATE-TRACE-REFERENCE", path, label + " must name at least one repository file"
        )
        return []
    valid: list[str] = []
    for value in values:
        if not text(value) or not repo_file_exists(repo, value):
            issue(
                report,
                "GATE-TRACE-REFERENCE",
                path,
                label + " references no repository file: " + str(value),
            )
        else:
            valid.append(value)
    return valid


def check_engineering(
    report: dict[str, Any],
    repo: Path,
    change_dir: Path,
    record: dict[str, Any],
    requirements: set[str] | None,
    verification: dict[str, dict[str, Any]],
) -> None:
    path = change_dir / GATE_RECORD
    rows = record.get("engineering")
    if not isinstance(rows, list):
        issue(report, "GATE-TRACE-ENGINEERING", path, "engineering traceability must be a list")
        check(report, "engineering traceability", False, "record missing")
        return
    seen: set[str] = set()
    accepted_statuses = TRACE_STATES
    for row in rows:
        if not isinstance(row, dict):
            issue(report, "GATE-TRACE-ENGINEERING", path, "engineering rows must be objects")
            continue
        identifier = row.get("requirement")
        if not text(identifier) or identifier in seen:
            issue(
                report,
                "GATE-TRACE-ENGINEERING",
                path,
                "requirement keys must be non-empty and unique",
            )
            continue
        seen.add(identifier)
        status = row.get("status")
        if not text(status) or status not in accepted_statuses:
            issue(report, "GATE-TRACE-ENGINEERING", path, identifier + " has an unknown status")
            continue
        if status == "UNVERIFIED":
            issue(report, "GATE-TRACE-UNVERIFIED", path, identifier + " remains UNVERIFIED")
        if status in {"PARTIALLY_VERIFIED", "NOT_APPLICABLE"}:
            if not text(row.get("gap")):
                issue(report, "GATE-TRACE-GAP", path, identifier + " needs a reason for " + status)
            if status == "PARTIALLY_VERIFIED":
                warn(report, "GATE-TRACE-PARTIAL", path, identifier + " is only partially verified")
        if status == "VERIFIED":
            check_paths(
                report, repo, path, row.get("implementation"), identifier + " implementation"
            )
            check_paths(report, repo, path, row.get("tests"), identifier + " tests")
            references = row.get("verification")
            if not isinstance(references, list) or not references:
                issue(
                    report,
                    "GATE-TRACE-EVIDENCE",
                    path,
                    identifier + " has no verification evidence ids",
                )
            else:
                for reference in references:
                    if not text(reference) or reference not in verification:
                        issue(
                            report,
                            "GATE-TRACE-EVIDENCE",
                            path,
                            identifier + " cites unknown verification id: " + str(reference),
                        )
    if requirements is not None:
        missing = requirements - seen
        extra = seen - requirements
        for identifier in sorted(missing):
            issue(report, "GATE-TRACE-COVERAGE", path, "missing requirement mapping: " + identifier)
        for identifier in sorted(extra):
            issue(
                report,
                "GATE-TRACE-COVERAGE",
                path,
                "mapping is not in OpenSpec delta output: " + identifier,
            )
    else:
        warn(
            report,
            "GATE-TRACE-COVERAGE-SKIPPED",
            path,
            "requirement coverage cannot be checked without OpenSpec CLI output",
        )
    check(
        report,
        "engineering traceability",
        not any(item["code"].startswith("GATE-TRACE-") for item in report["errors"]),
        str(len(seen)) + " mapped requirement(s)",
    )


def check_science(
    report: dict[str, Any],
    repo: Path,
    change_dir: Path,
    record: dict[str, Any],
    verification: dict[str, dict[str, Any]],
) -> None:
    path = change_dir / GATE_RECORD
    science = record.get("science")
    if not isinstance(science, dict) or not isinstance(science.get("applicable"), bool):
        issue(
            report,
            "GATE-SCIENCE-APPLICABILITY",
            path,
            "science.applicable must explicitly be true or false",
        )
        check(report, "scientific traceability", False, "applicability missing")
        return
    claims = science.get("claims")
    if not isinstance(claims, list):
        issue(report, "GATE-SCIENCE-CLAIMS", path, "science.claims must be a list")
        claims = []
    if not science["applicable"]:
        if not text(science.get("reason")):
            issue(report, "GATE-SCIENCE-APPLICABILITY", path, "non-applicability needs a reason")
        if claims:
            issue(
                report,
                "GATE-SCIENCE-APPLICABILITY",
                path,
                "non-applicable science must not contain scientific claims",
            )
    else:
        if not claims:
            issue(
                report,
                "GATE-SCIENCE-MISSING",
                path,
                "scientific changes need at least one traceability row",
            )
        evidence_ids: set[str] = set()
        for claim in claims:
            if not isinstance(claim, dict):
                issue(report, "GATE-SCIENCE-CLAIM", path, "scientific claims must be objects")
                continue
            identifier = claim.get("evidence_id")
            if not text(identifier) or identifier in evidence_ids:
                issue(report, "GATE-SCIENCE-ID", path, "evidence ids must be explicit and unique")
                continue
            evidence_ids.add(identifier)
            source = claim.get("source")
            source_path = Path(source) if text(source) else Path()
            evidence_root = (repo / EVIDENCE_DIR).resolve()
            try:
                candidate = (repo / source_path).resolve()
                source_is_evidence = candidate.is_relative_to(evidence_root) and candidate.is_file()
                if source_is_evidence:
                    source_is_evidence = (
                        "- Evidence ID: " + identifier
                        in candidate.read_text(encoding="utf-8").splitlines()
                    )
            except (OSError, RuntimeError, UnicodeError):
                source_is_evidence = False
            if not source_is_evidence:
                issue(
                    report,
                    "GATE-SCIENCE-SOURCE",
                    path,
                    identifier + " must match an exact Evidence ID in a file under docs/evidence/",
                )
            for field in ("assumption", "parameter", "model"):
                if not text(claim.get(field)):
                    issue(report, "GATE-SCIENCE-CLAIM", path, identifier + " has no " + field)
            data_class = claim.get("data_class")
            if not text(data_class) or data_class not in DATA_CLASSES:
                issue(report, "GATE-SCIENCE-CLASS", path, identifier + " has an unknown data_class")
            state = claim.get("status")
            if not text(state) or state not in TRACE_STATES - {"NOT_APPLICABLE"}:
                issue(report, "GATE-SCIENCE-STATUS", path, identifier + " has an unknown status")
                continue
            if state == "UNVERIFIED":
                issue(report, "GATE-SCIENCE-UNVERIFIED", path, identifier + " remains UNVERIFIED")
            if claim.get("data_class") == "UNVERIFIED" and state == "VERIFIED":
                issue(
                    report,
                    "GATE-SCIENCE-STATUS",
                    path,
                    identifier + " cannot mark UNVERIFIED data as VERIFIED",
                )
            if state in {"PARTIALLY_VERIFIED", "UNVERIFIED"}:
                if not text(claim.get("limitation")):
                    issue(
                        report,
                        "GATE-SCIENCE-LIMITATION",
                        path,
                        identifier + " must record its limitation",
                    )
                if state == "PARTIALLY_VERIFIED":
                    warn(
                        report,
                        "GATE-SCIENCE-PARTIAL",
                        path,
                        identifier + " is only partially verified",
                    )
            validations = claim.get("validation")
            if not isinstance(validations, list) or not validations:
                issue(
                    report,
                    "GATE-SCIENCE-EVIDENCE",
                    path,
                    identifier + " has no validation evidence ids",
                )
            else:
                for reference in validations:
                    if not text(reference) or reference not in verification:
                        issue(
                            report,
                            "GATE-SCIENCE-EVIDENCE",
                            path,
                            identifier + " cites unknown verification id: " + str(reference),
                        )
    check(
        report,
        "scientific traceability",
        not any(item["code"].startswith("GATE-SCIENCE-") for item in report["errors"]),
        "applicable" if science["applicable"] else "not applicable",
    )


def check_approval(
    report: dict[str, Any], change_dir: Path, record: dict[str, Any], accepted_findings: set[str]
) -> None:
    path = change_dir / GATE_RECORD
    approval = record.get("approval")
    if approval is None:
        if accepted_findings:
            issue(
                report,
                "GATE-APPROVAL-MISSING",
                path,
                "accepted-risk findings need approval tied to each finding",
            )
        check(
            report,
            "human approval",
            not accepted_findings,
            "not required" if not accepted_findings else "accepted risk has no approval",
        )
        return
    if not isinstance(approval, dict) or not isinstance(approval.get("required"), bool):
        issue(
            report,
            "GATE-APPROVAL-STATE",
            path,
            "approval must be null or an object with required: true/false",
        )
        check(report, "human approval", False, "invalid state")
        return
    if not approval["required"]:
        if accepted_findings:
            issue(
                report, "GATE-APPROVAL-MISSING", path, "accepted-risk findings need human approval"
            )
        check(
            report,
            "human approval",
            not accepted_findings,
            "not required" if not accepted_findings else "accepted risk has no approval",
        )
        return

    before = len(report["errors"])
    record_path = change_dir / "verification" / "acceptance.md"
    if not nonempty_file(record_path):
        issue(
            report,
            "GATE-APPROVAL-RECORD",
            record_path,
            "required human acceptance record is missing",
        )
    if not text(approval.get("trigger")) or approval["trigger"] not in APPROVAL_TRIGGERS:
        issue(report, "GATE-APPROVAL-TRIGGER", path, "approval trigger is missing or unsupported")
    if approval.get("decision") != "APPROVED":
        issue(report, "GATE-APPROVAL-DECISION", path, "required human decision is not APPROVED")
    for field in ("approver", "reference", "scope"):
        if not text(approval.get(field)):
            issue(report, "GATE-APPROVAL-FIELD", path, "required approval has no " + field)
    findings = approval.get("findings", [])
    if not isinstance(findings, list) or any(not text(item) for item in findings):
        issue(
            report,
            "GATE-APPROVAL-FINDINGS",
            path,
            "approval findings must be a list of finding ids",
        )
        findings = []
    if len(findings) != len(set(findings)):
        issue(report, "GATE-APPROVAL-FINDINGS", path, "approval finding ids must be unique")
    if set(findings) != accepted_findings:
        issue(
            report,
            "GATE-APPROVAL-FINDINGS",
            path,
            "approval must name exactly the accepted-risk findings",
        )
    check(
        report,
        "human approval",
        len(report["errors"]) == before,
        "required: " + str(approval["required"]),
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check RatSight OpenSpec evidence state before archive."
    )
    parser.add_argument("change", nargs="?", help="change under openspec/changes/")
    parser.add_argument("--repo-root", help="repository root; default: nearest openspec/ directory")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    parser.add_argument(
        "--allow-no-change", action="store_true", help="pass when no active changes exist"
    )
    parser.add_argument(
        "--skip-openspec",
        action="store_true",
        help="skip OpenSpec CLI checks; records a limitation",
    )
    return parser


def emit(report: dict[str, Any], as_json: bool) -> None:
    payload = {
        "change": report["change"],
        "repo": str(report["repo"]),
        "passed": not report["errors"],
        "checks": report["checks"],
        "errors": report["errors"],
        "warnings": report["warnings"],
        "note": (
            "the gate checks recorded state and references; it does not authenticate reviews, "
            "command execution, human approval, or scientific validity"
        ),
    }
    if as_json:
        print(json.dumps(payload, indent=2))
        return
    print("RatSight OpenSpec quality gate: " + report["change"])
    for item in report["checks"]:
        print("[" + item["status"].upper() + "] " + item["name"] + " - " + item["detail"])
    for label in ("errors", "warnings"):
        for item in report[label]:
            print(
                label[:-1].upper()
                + " "
                + item["code"]
                + " "
                + item["path"]
                + ": "
                + item["message"]
            )
    print("RESULT: " + ("PASS" if not report["errors"] else "BLOCKED"))
    print("Recorded references and judgments are not authenticated by this gate.")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    repo = Path(args.repo_root).resolve() if args.repo_root else find_repo(Path.cwd())
    if repo is None:
        print("quality gate: no openspec/ directory found", file=sys.stderr)
        return EXIT_USAGE
    changes = active_changes(repo)
    change = args.change
    if change is None:
        if not changes:
            message = "quality gate: no active change under " + str(repo / CHANGES)
            if args.allow_no_change:
                print(message + " - nothing to gate")
                return EXIT_PASS
            print(message + "; pass a change name or --allow-no-change", file=sys.stderr)
            return EXIT_USAGE
        if len(changes) != 1:
            print(
                "quality gate: name one change; active changes: " + ", ".join(changes),
                file=sys.stderr,
            )
            return EXIT_USAGE
        change = changes[0]
    if Path(change).name != change or change in {".", ".."}:
        print("quality gate: change must be a directory name", file=sys.stderr)
        return EXIT_USAGE
    change_dir = repo / CHANGES / change
    if not change_dir.is_dir():
        print("quality gate: no such change: " + str(change_dir), file=sys.stderr)
        return EXIT_USAGE

    report: dict[str, Any] = {
        "change": change,
        "repo": repo,
        "checks": [],
        "errors": [],
        "warnings": [],
    }
    requirements = check_openspec(report, repo, change, args.skip_openspec)
    record = load_gate_record(report, change_dir)
    accepted: set[str] = set()
    if record is not None:
        verification = check_verification(report, change_dir, record)
        reviews = record.get("reviews")
        ar_ids, ar_accepted = check_review(
            report, change_dir, reviews, "adversarial", "adversarial-review.md", "GATE-AR"
        )
        cr_ids, cr_accepted = check_review(
            report, change_dir, reviews, "code", "verification/code-review.md", "GATE-CR"
        )
        if ar_ids & cr_ids:
            issue(
                report,
                "GATE-FINDING-ID",
                change_dir / GATE_RECORD,
                "finding ids must be unique across reviews",
            )
        accepted = set(ar_accepted + cr_accepted)
        check_engineering(report, repo, change_dir, record, requirements, verification)
        check_science(report, repo, change_dir, record, verification)
        check_approval(report, change_dir, record, accepted)

    emit(report, args.json)
    return EXIT_PASS if not report["errors"] else EXIT_BLOCKED


if __name__ == "__main__":
    sys.exit(main())
