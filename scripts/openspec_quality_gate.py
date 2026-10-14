#!/usr/bin/env python3
"""Deterministic, evidence-based quality gate for RatSight OpenSpec changes.

Usage:
    python3 scripts/openspec_quality_gate.py <change-name>
    python3 scripts/openspec_quality_gate.py            # autodetect one change
    python3 scripts/openspec_quality_gate.py <name> --json
    python3 scripts/openspec_quality_gate.py --allow-no-change

Exit codes:
    0  gate passed (warnings may still be present)
    1  gate blocked: at least one error
    2  usage, unsupported interpreter, or repository state error

Requires Python 3.10 or newer; the repository's uv environment provides 3.12.
The gate is pure standard library and needs no agent runtime.

What this gate is, and is not
-----------------------------
It evaluates recorded evidence: the planning artifacts, the adversarial review,
the independent code review, the traceability report, the acceptance record, and
the OpenSpec CLI's own validation. It checks presence, required fields, allowed
enum values, stable-identifier coverage, cross-record consistency, and that a
claimed executed command was recorded.

It does not verify that a review was performed honestly, that a reviewer was
truly independent, or that a test summary is truthful. A record can be complete
and still false; the gate raises the cost of claiming completion without a
recorded basis, and nothing more. Do not read a passing gate as an independent
review.

Enforcement split (see guidance/openspec-workflow.md):
    schema-enforced     planning artifacts and their ordering (OpenSpec CLI)
    script-enforced     the checks in this file
    guidance-only       performing the reviews and QA honestly
    human-controlled    approval, waivers, and the archive decision

Runtime independence: this gate reads repository files and the OpenSpec CLI
only. It never contacts an agent runtime, so it behaves identically under a
standalone coding agent, Codex, Claude Code, or an orchestrated fleet. Identity
fields in the records (reviewer, implementer, approver, independence
mechanism) are provenance the recorder chooses; no runtime name, session id, or
orchestration API is required by any check.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

if sys.version_info < (3, 10):  # noqa: UP036 - the gate also runs under a system interpreter
    sys.stderr.write(
        "openspec_quality_gate.py requires Python 3.10 or newer; found "
        + ".".join(str(part) for part in sys.version_info[:3])
        + ". Run it with 'uv run python scripts/openspec_quality_gate.py'."
        + chr(10)
    )
    raise SystemExit(2)

EXIT_PASS = 0
EXIT_BLOCKED = 1
EXIT_USAGE = 2

SCHEMA_NAME = "evidence-driven"
SCHEMA_REL = Path("openspec") / "schemas" / SCHEMA_NAME
CHANGES_REL = Path("openspec") / "changes"
EVIDENCE_REL = Path("docs") / "evidence"
TEMPLATE_REL = SCHEMA_REL / "templates"

#: Planning artifacts the evidence-driven schema declares. Kept in sync with
#: openspec/schemas/evidence-driven/schema.yaml and asserted against it at run
#: time, so a schema edit this gate does not understand fails loudly.
EXPECTED_ARTIFACTS = {
    "proposal": "proposal.md",
    "specs": "specs/**/*.md",
    "design": "design.md",
    "adversarial-review": "adversarial-review.md",
    "tasks": "tasks.md",
}
PLANNING_FILES = ("proposal.md", "design.md", "adversarial-review.md", "tasks.md")

REVIEW_DECISIONS = ("PASS", "PASS_WITH_WARNINGS", "BLOCKED")
TRACE_STATUSES = ("VERIFIED", "PARTIALLY_VERIFIED", "UNVERIFIED", "NOT_APPLICABLE")
DATA_CLASSES = ("OBSERVED", "INFERRED", "SIMULATED", "UNVERIFIED")
SEVERITIES = ("BLOCKING", "MAJOR", "MINOR", "INFO")
FINDING_STATUSES = ("OPEN", "RESOLVED", "ACCEPTED_RISK", "DEFERRED")
INDEPENDENCE = (
    "SEPARATE_SESSION",
    "SEPARATE_WORKTREE",
    "SEPARATE_AGENT",
    "SEPARATE_MODEL",
    "HUMAN",
    "NONE",
)
ACCEPTANCE_TRIGGERS = (
    "NONE",
    "ARCHITECTURE_CHANGE",
    "NEW_SCIENTIFIC_ASSUMPTION",
    "UNKNOWN_PARAMETER_DEFAULT",
    "SENSITIVE_DATA_POLICY",
    "ACCEPTANCE_EXCEPTION",
)
ACCEPTANCE_DECISIONS = ("APPROVED", "REJECTED", "PENDING")

#: Narrow literal guard for the project's primary integrity rule: simulated
#: output must never be described as an observation. This is a phrase check,
#: not semantic analysis.
SIMULATED_FORBIDDEN_PHRASES = (
    "observed migration",
    "observed route",
    "observed movement",
    "observed count",
    "real-world observation",
    "actual observation",
)

BACKTICK = chr(96)

ANGLE_VALUE_RE = re.compile(r"^<.*>$")
ISO_DATE_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
FIELD_RE = re.compile(
    r"^\s*[-*+]\s*\*{0,2}([A-Za-z][A-Za-z0-9 /()_.,'-]{0,80}?)\*{0,2}\s*:\s*(.*?)\s*$"
)
CHECKBOX_RE = re.compile(r"^\s*[-*]\s+\[(?P<mark>[^\]]*)\]\s*(?P<text>.*?)\s*$")
COMMAND_RE = re.compile(BACKTICK + r"([^" + BACKTICK + r"]+)" + BACKTICK)
REQUIREMENT_RE = re.compile(r"^#{3}\s+Requirement:\s*(.+?)\s*$", re.MULTILINE)
SCENARIO_RE = re.compile(r"^#{4}\s+Scenario:\s*(.+?)\s*$", re.MULTILINE)
PATH_LIKE_RE = re.compile(
    r"[A-Za-z0-9_./-]+\.(py|ts|tsx|js|mjs|cjs|json|yaml|yml|md|toml|sql|sh|css|html)\b"
)
NONE_LINE_RE = re.compile(r"^\s*[-*]\s+(none\.?|not applicable\.?)\s*$", re.IGNORECASE)

PLACEHOLDER_TOKENS = {
    "",
    "-",
    "--",
    "---",
    "...",
    "?",
    "??",
    "???",
    "tbd",
    "tba",
    "tbc",
    "todo",
    "n/a",
    "na",
    "nan",
    "unknown",
    "<placeholder>",
}
STRICT_ONLY_TOKENS = {"none", "nil", "null", "same", "same as above"}


@dataclass
class Issue:
    """One gate finding: an error blocks the change, a warning does not."""

    code: str
    severity: str
    path: str
    message: str


@dataclass
class Check:
    """A named check and its outcome, reported to the operator."""

    name: str
    status: str
    detail: str


@dataclass
class Report:
    """Collects issues and check outcomes for one gate run."""

    repo: Path
    change: str
    issues: list = field(default_factory=list)
    checks: list = field(default_factory=list)

    def error(self, code: str, path, message: str) -> None:
        self.issues.append(Issue(code, "error", str(path), message))

    def warn(self, code: str, path, message: str) -> None:
        self.issues.append(Issue(code, "warning", str(path), message))

    def check(self, name: str, status: str, detail: str = "") -> None:
        self.checks.append(Check(name, status, detail))

    @property
    def errors(self) -> list:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> list:
        return [i for i in self.issues if i.severity == "warning"]

    @property
    def passed(self) -> bool:
        return not self.errors


# --------------------------------------------------------------------------- #
# parsing helpers
# --------------------------------------------------------------------------- #


def normalize(text: str) -> str:
    """Lowercase and collapse non-alphanumeric runs, for forgiving key matching."""
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def slug(text: str) -> str:
    """Stable identifier fragment for a heading: lowercase, dash-separated."""
    return re.sub(r"-{2,}", "-", re.sub(r"[^a-z0-9]+", "-", text.lower())).strip("-")


def is_placeholder(value, strict: bool = True) -> bool:
    """Whether a field value is empty, a template marker, or a filler token."""
    if value is None:
        return True
    text = value.strip().strip(BACKTICK).strip()
    text = text.strip("*_").strip()
    if ANGLE_VALUE_RE.match(text):
        return True
    token = text.lower().strip().rstrip(".")
    if token in PLACEHOLDER_TOKENS:
        return True
    return strict and token in STRICT_ONLY_TOKENS


def normalize_identity(value: str) -> str:
    """Comparable identity for a person/agent/session field, ignoring role notes."""
    text = normalize(value)
    for marker in (" agent", " reviewer", " implementer", " session"):
        index = text.find(marker)
        if index > 0:
            text = text[:index]
    return text


def iter_sections(text: str) -> list:
    """Return (title, body, level) for every heading in a document."""
    sections = []
    title = None
    level = 0
    buffer: list = []
    for line in text.splitlines():
        match = HEADING_RE.match(line)
        if match:
            if title is not None:
                sections.append((title, "\n".join(buffer), level))
            title = match.group(2).strip()
            level = len(match.group(1))
            buffer = []
        elif title is not None:
            buffer.append(line)
    if title is not None:
        sections.append((title, "\n".join(buffer), level))
    return sections


def find_section(report: Report, path, text: str, title: str):
    """Return the body of a unique heading, recording an error otherwise."""
    wanted = normalize(title)
    matches = [body for name, body, _level in iter_sections(text) if normalize(name) == wanted]
    if not matches:
        report.error("GATE-SECTION-MISSING", path, "missing section '## " + title + "'")
        return None
    if len(matches) > 1:
        report.error(
            "GATE-SECTION-DUPLICATE",
            path,
            "section '## " + title + "' appears " + str(len(matches)) + " times",
        )
        return matches[0]
    return matches[0]


def parse_fields(body: str) -> list:
    """Return (key, value) pairs for bullet or bold 'Key: value' lines."""
    pairs = []
    for line in body.splitlines():
        if line.lstrip().startswith(("|", "#", ">")):
            continue
        match = FIELD_RE.match(line)
        if match:
            pairs.append((match.group(1).strip(), match.group(2).strip()))
    return pairs


def field_values(pairs: list, prefix: str) -> list:
    """All values whose key starts with prefix, case-insensitive."""
    wanted = normalize(prefix)
    return [value for key, value in pairs if normalize(key).startswith(wanted)]


def one_field(
    report: Report, code: str, path, pairs: list, prefix: str, label: str, strict: bool = True
):
    """Require exactly one non-placeholder value for a required field."""
    values = field_values(pairs, prefix)
    if not values:
        report.error(code, path, "missing field '" + label + "'")
        return None
    if len(values) > 1:
        report.error(
            code,
            path,
            "field '" + label + "' is recorded " + str(len(values)) + " times; keep exactly one",
        )
        return None
    if is_placeholder(values[0], strict=strict):
        report.error(
            code, path, "field '" + label + "' is empty or still a placeholder: " + repr(values[0])
        )
        return None
    return values[0].strip()


def enum_value(report: Report, code: str, path, raw, allowed, label: str):
    """Require one value from a fixed vocabulary, rejecting unfilled option lists."""
    if raw is None:
        return None
    if "|" in raw:
        report.error(code, path, "field '" + label + "' still lists unfilled options: " + repr(raw))
        return None
    token = re.split(r"[\s,;.()]+", raw.strip().strip("*_"))[0].upper()
    if token not in allowed:
        report.error(
            code, path, "field '" + label + "' is " + repr(raw) + "; allowed: " + ", ".join(allowed)
        )
        return None
    return token


def enum_field(report: Report, code: str, path, pairs: list, prefix: str, label: str, allowed):
    raw = one_field(report, code, path, pairs, prefix, label, strict=False)
    return enum_value(report, code, path, raw, allowed, label)


def split_row(line: str) -> list:
    """Split a Markdown table row on unescaped pipes."""
    stripped = line.strip().strip("|")
    return [cell.strip().replace("\\|", "|") for cell in re.split(r"(?<!\\)\|", stripped)]


def is_separator_row(line: str) -> bool:
    cells = [cell for cell in split_row(line) if cell]
    if len(cells) < 2:
        return False
    return all(re.fullmatch(r":?-{2,}:?", cell.replace(" ", "")) for cell in cells)


def parse_tables(body: str) -> list:
    """Return every Markdown table in a section as {headers, rows}."""
    lines = body.splitlines()
    tables = []
    index = 0
    while index < len(lines):
        if (
            lines[index].count("|") >= 2
            and index + 1 < len(lines)
            and is_separator_row(lines[index + 1])
        ):
            headers = split_row(lines[index])
            rows = []
            cursor = index + 2
            while (
                cursor < len(lines)
                and lines[cursor].count("|") >= 2
                and not is_separator_row(lines[cursor])
            ):
                cells = split_row(lines[cursor])
                while len(cells) < len(headers):
                    cells.append("")
                rows.append(dict(zip(headers, cells, strict=False)))
                cursor += 1
            tables.append({"headers": headers, "rows": rows})
            index = cursor
        else:
            index += 1
    return tables


def column(table: dict, token: str):
    """Header whose normalized form contains token, or None."""
    wanted = normalize(token)
    for header in table["headers"]:
        if wanted in normalize(header):
            return header
    return None


def require_table(report: Report, code: str, path, body, title: str, columns: list):
    """Find a table containing every required column, or record an error."""
    tables = parse_tables(body)
    if not tables:
        report.error(
            code,
            path,
            "section '" + title + "' has no table; expected columns: " + ", ".join(columns),
        )
        return None
    for table in tables:
        if all(column(table, name) for name in columns):
            return table
    found = " | ".join(tables[0]["headers"])
    report.error(
        code,
        path,
        "no table in '"
        + title
        + "' has the required columns ("
        + ", ".join(columns)
        + "); found: "
        + found,
    )
    return None


def cell(row: dict, table: dict, token: str) -> str:
    header = column(table, token)
    return (row.get(header, "") or "").strip() if header else ""


def commands_in(text: str) -> list:
    """Every backticked command in a cell."""
    return [match.strip() for match in COMMAND_RE.findall(text or "")]


# --------------------------------------------------------------------------- #
# repository and schema
# --------------------------------------------------------------------------- #


def resolve_repo_root(start: Path) -> Path | None:
    candidate = start.resolve()
    for directory in [candidate, *candidate.parents]:
        if (directory / "openspec").is_dir():
            return directory
    return None


def active_changes(repo: Path) -> list:
    changes_dir = repo / CHANGES_REL
    if not changes_dir.is_dir():
        return []
    return sorted(
        entry.name
        for entry in changes_dir.iterdir()
        if entry.is_dir() and entry.name != "archive" and not entry.name.startswith(".")
    )


def schema_artifacts(schema_file: Path) -> dict:
    """Map artifact id -> {generates, requires} from schema.yaml, without PyYAML."""
    artifacts: dict = {}
    current = None
    in_requires = False
    for line in schema_file.read_text(encoding="utf-8").splitlines():
        if re.match(r"^\S", line):
            # A top-level key (name:, artifacts:, apply:, ...) ends the artifact
            # list. Without this reset, apply.requires would overwrite the last
            # artifact's requires list and the drift check would misfire.
            current = None
            in_requires = False
            continue
        id_match = re.match(r"^\s{2,4}-\s+id:\s*(\S+)\s*$", line)
        if id_match:
            current = id_match.group(1)
            artifacts[current] = {"generates": None, "requires": []}
            in_requires = False
            continue
        if current is None:
            continue
        generates_match = re.match(r"^\s+generates:\s*(.+?)\s*$", line)
        if generates_match:
            artifacts[current]["generates"] = generates_match.group(1).strip().strip('"')
            in_requires = False
            continue
        if re.match(r"^\s+requires:\s*$", line):
            in_requires = True
            continue
        if re.match(r"^\s+requires:\s*\[", line):
            inner = line.split("[", 1)[1].split("]", 1)[0]
            artifacts[current]["requires"] = [
                item.strip() for item in inner.split(",") if item.strip()
            ]
            in_requires = False
            continue
        if in_requires:
            item_match = re.match(r"^\s+-\s+(\S+)\s*$", line)
            if item_match:
                artifacts[current]["requires"].append(item_match.group(1))
            elif line.strip():
                in_requires = False
    return artifacts


def check_schema(report: Report, repo: Path) -> None:
    """Assert this gate and the schema agree, and that ordering is as intended."""
    schema_file = repo / SCHEMA_REL / "schema.yaml"
    if not schema_file.is_file():
        report.error("GATE-SCHEMA-MISSING", schema_file, "schema.yaml not found")
        report.check("schema drift", "fail", "schema.yaml missing")
        return
    artifacts = schema_artifacts(schema_file)
    problems = []
    for artifact_id, generates in EXPECTED_ARTIFACTS.items():
        found = artifacts.get(artifact_id)
        if found is None:
            problems.append("artifact '" + artifact_id + "' is declared but not in schema.yaml")
        elif found["generates"] != generates:
            problems.append(
                "artifact '"
                + artifact_id
                + "' generates "
                + repr(found["generates"])
                + ", this gate expects "
                + repr(generates)
            )
    review = artifacts.get("adversarial-review", {}).get("requires", [])
    if sorted(review) != ["design", "specs"]:
        problems.append(
            "adversarial-review must require exactly specs and design, found " + repr(review)
        )
    tasks_requires = artifacts.get("tasks", {}).get("requires", [])
    if "adversarial-review" not in tasks_requires:
        problems.append("tasks must require adversarial-review, found " + repr(tasks_requires))
    if problems:
        for problem in problems:
            report.error("GATE-SCHEMA-DRIFT", schema_file, problem)
        report.check("schema drift", "fail", str(len(problems)) + " mismatch(es)")
    else:
        report.check("schema drift", "ok", "gate matches schema.yaml")


def check_planning_artifacts(report: Report, change_dir: Path) -> None:
    """Presence of the schema's planning artifacts, and whether specs are opted out."""
    missing = []
    empty = []
    for name in PLANNING_FILES:
        candidate = change_dir / name
        if not candidate.is_file():
            missing.append(name)
            continue
        text = candidate.read_text(encoding="utf-8", errors="replace")
        body = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
        if not body.strip():
            empty.append(name)
    for name in missing:
        report.error(
            "GATE-ARTIFACT-MISSING",
            change_dir / name,
            "planning artifact missing (see openspec instructions " + name.split(".")[0] + ")",
        )
    for name in empty:
        report.error(
            "GATE-ARTIFACT-EMPTY",
            change_dir / name,
            "planning artifact has no content outside comments",
        )

    skip_specs = False
    metadata = change_dir / ".openspec.yaml"
    if metadata.is_file():
        skip_specs = bool(
            re.search(
                r"^\s*skip_specs:\s*true\s*$", metadata.read_text(encoding="utf-8"), re.MULTILINE
            )
        )
    spec_files = (
        sorted((change_dir / "specs").rglob("*.md")) if (change_dir / "specs").is_dir() else []
    )
    if skip_specs:
        report.check("planning artifacts", "ok", "skip_specs: true, specs not required")
        return
    if not spec_files:
        report.error(
            "GATE-SPECS-MISSING",
            change_dir / "specs",
            "no delta spec files under specs/; create one per capability or set skip_specs: true",
        )
    elif not any(
        REQUIREMENT_RE.search(path.read_text(encoding="utf-8", errors="replace"))
        for path in spec_files
    ):
        report.error(
            "GATE-SPECS-EMPTY",
            change_dir / "specs",
            "no '### Requirement:' heading in any delta spec",
        )
    else:
        report.check("planning artifacts", "ok", str(len(spec_files)) + " delta spec file(s)")


def check_tasks_complete(report: Report, change_dir: Path) -> None:
    """Every tracked task must be checked off before archive."""
    tasks_file = change_dir / "tasks.md"
    if not tasks_file.is_file():
        return
    unfinished = []
    total = 0
    for number, line in enumerate(
        tasks_file.read_text(encoding="utf-8", errors="replace").splitlines(), start=1
    ):
        match = CHECKBOX_RE.match(line)
        if not match:
            continue
        total += 1
        if match.group("mark").strip().lower() != "x":
            unfinished.append((number, match.group("text")[:60]))
    if total == 0:
        report.error(
            "GATE-TASKS-NONE",
            tasks_file,
            "no tracked task checkbox found; apply tracks tasks.md checkboxes",
        )
    elif unfinished:
        preview = "; ".join("line " + str(number) + ": " + text for number, text in unfinished[:3])
        report.error(
            "GATE-TASKS-OPEN",
            tasks_file,
            str(len(unfinished)) + " of " + str(total) + " tasks are unfinished (" + preview + ")",
        )
    else:
        report.check("tasks complete", "ok", str(total) + " task(s) checked")


# --------------------------------------------------------------------------- #
# spec coverage
# --------------------------------------------------------------------------- #


@dataclass
class SpecRequirement:
    """A requirement from a delta spec, with its stable identifier."""

    identifier: str
    scenarios: list
    source: str


def collect_requirements(report: Report, change_dir: Path) -> dict:
    """Requirement identifiers from the change's delta specs, keyed for coverage."""
    specs_dir = change_dir / "specs"
    requirements: dict = {}
    if not specs_dir.is_dir():
        return requirements
    for spec_file in sorted(specs_dir.rglob("*.md")):
        relative = spec_file.relative_to(specs_dir)
        capability = relative.parent.as_posix()
        current = None
        for line in spec_file.read_text(encoding="utf-8", errors="replace").splitlines():
            requirement_match = REQUIREMENT_RE.match(line)
            if requirement_match:
                identifier = capability + "#" + slug(requirement_match.group(1))
                current = identifier
                requirements[identifier] = SpecRequirement(
                    identifier, [], str(spec_file.relative_to(change_dir.parent.parent))
                )
                continue
            scenario_match = SCENARIO_RE.match(line)
            if scenario_match and current is not None:
                requirements[current].scenarios.append(
                    current + "/" + slug(scenario_match.group(1))
                )
    if not requirements:
        report.check("spec coverage", "skip", "no delta requirements to map")
    else:
        report.check(
            "spec coverage", "ok", str(len(requirements)) + " requirement identifier(s) to map"
        )
    return requirements


# --------------------------------------------------------------------------- #
# adversarial review
# --------------------------------------------------------------------------- #

ADVERSARIAL_SCOPE = (
    "Requirements",
    "Architecture",
    "Scientific assumptions",
    "Evidence quality",
    "Acceptance criteria",
    "Failure scenarios",
)
ADVERSARIAL_SECTIONS = (
    "Review Record",
    "Review Scope",
    "Assumption Challenges",
    "Requirement Gaps",
    "Design Counterexamples",
    "Scientific Validity",
    "Acceptance Criteria Weaknesses",
    "Findings",
    "Review Decision",
)


def check_disposition(report: Report, code: str, path, label: str, value_prefix: str) -> None:
    """A reviewed/not-applicable disposition with a usable value."""
    if value_prefix is None:
        report.error(code, path, "no entry for '" + label + "'")
        return
    normalized = normalize(value_prefix)
    if normalized.startswith("not applicable"):
        reason = value_prefix[len("not applicable") :].strip(" -:")
        if is_placeholder(reason, strict=False):
            report.error(code, path, "'" + label + "' is Not applicable with no reason")
        return
    if normalized.startswith("reviewed"):
        return
    report.error(
        code,
        path,
        "'"
        + label
        + "' must be marked 'Reviewed' or 'Not applicable - <reason>', found "
        + repr(value_prefix),
    )


def check_findings_table(
    report: Report,
    path,
    body: str,
    title: str,
    evidence_token: str,
    action_token: str,
    location_token=None,
):
    """Validate a findings table and return (rows, unresolved_blocking)."""
    header = [
        "Finding ID",
        "Severity",
        location_token or "Affected artifact",
        "Description",
        evidence_token,
        action_token,
        "Status",
    ]
    if location_token is None:
        header = [
            "Finding ID",
            "Severity",
            "Affected artifact",
            evidence_token,
            action_token,
            "Status",
        ]
    table = require_table(
        report,
        "GATE-" + title.upper().replace(" ", "-") + "-COLUMNS",
        path,
        body,
        title,
        [name for name in header],
    )
    if table is None:
        return [], 0, False
    rows = []
    unresolved_blocking = 0
    accepted_blocking = False
    seen_ids = set()
    for row in table["rows"]:
        cells = {normalize(key): value for key, value in row.items()}
        finding_id = ""
        for key, value in cells.items():
            if "finding id" in key:
                finding_id = value.strip()
        if not re.fullmatch(r"[A-Za-z]{2,6}-\d+", finding_id):
            report.error(
                "GATE-FINDING-ID",
                path,
                "finding id " + repr(finding_id) + " must look like AR-1 or CR-2",
            )
            continue
        if finding_id in seen_ids:
            report.error(
                "GATE-FINDING-DUPLICATE", path, "finding id " + finding_id + " is used twice"
            )
            continue
        seen_ids.add(finding_id)
        severity = enum_value(
            report,
            "GATE-FINDING-SEVERITY",
            path,
            cell(row, table, "severity"),
            SEVERITIES,
            finding_id + " severity",
        )
        status = enum_value(
            report,
            "GATE-FINDING-STATUS",
            path,
            cell(row, table, "status"),
            FINDING_STATUSES,
            finding_id + " status",
        )
        if location_token is not None:
            location = cell(row, table, location_token)
            if is_placeholder(location, strict=False):
                report.error("GATE-FINDING-LOCATION", path, finding_id + " has no location")
            elif not (PATH_LIKE_RE.search(location) or re.search(r":\d+", location)):
                report.error(
                    "GATE-FINDING-LOCATION",
                    path,
                    finding_id + " location " + repr(location) + " names no file path or line",
                )
        else:
            affected = cell(row, table, "affected artifact")
            if is_placeholder(affected, strict=False):
                report.error(
                    "GATE-FINDING-ARTIFACT", path, finding_id + " names no affected artifact"
                )
        if location_token is not None:
            description = cell(row, table, "description")
            if is_placeholder(description, strict=False):
                report.error("GATE-FINDING-DESCRIPTION", path, finding_id + " has no description")
        evidence_value = cell(row, table, evidence_token)
        if is_placeholder(evidence_value, strict=False):
            report.error(
                "GATE-FINDING-EVIDENCE",
                path,
                finding_id + " has no reproduction or supporting evidence",
            )
        action = cell(row, table, action_token)
        if is_placeholder(action, strict=False):
            report.error(
                "GATE-FINDING-ACTION",
                path,
                finding_id + " has no proposed resolution or correction",
            )
        if severity == "BLOCKING":
            if status != "RESOLVED":
                unresolved_blocking += 1
                if status == "ACCEPTED_RISK":
                    accepted_blocking = True
                    if "waiver" not in normalize(action or ""):
                        report.error(
                            "GATE-FINDING-WAIVER",
                            path,
                            finding_id
                            + " is BLOCKING/ACCEPTED_RISK but records no waiver in its resolution",
                        )
        rows.append(
            {
                "id": finding_id,
                "severity": severity,
                "status": status,
                "row": row,
                "table": table,
            }
        )
    return rows, unresolved_blocking, accepted_blocking


def check_review_decision(
    report: Report, code: str, path, body: str, label: str, unresolved_blocking: int
) -> str | None:
    """Parse one Decision line and require it to match the findings table."""
    pairs = parse_fields(body)
    decision_code = "GATE-" + code + "-DECISION"
    raw = one_field(
        report, decision_code, path, pairs, "decision", label + " decision", strict=False
    )
    decision = enum_value(report, decision_code, path, raw, REVIEW_DECISIONS, label + " decision")
    reported_open = one_field(
        report,
        "GATE-DECISION-COUNT",
        path,
        pairs,
        "blocking findings open",
        label + " open blocking count",
        strict=False,
    )
    if reported_open is not None:
        count_match = re.search(r"\d+", reported_open)
        if not count_match:
            report.error(
                "GATE-DECISION-COUNT",
                path,
                "'Blocking findings open' is not an integer: " + repr(reported_open),
            )
        elif int(count_match.group(0)) != unresolved_blocking:
            report.error(
                "GATE-DECISION-COUNT",
                path,
                "'Blocking findings open' says "
                + count_match.group(0)
                + " but the findings table has "
                + str(unresolved_blocking)
                + " unresolved BLOCKING finding(s)",
            )
    if decision == "BLOCKED":
        report.error(
            "GATE-" + code + "-BLOCKED",
            path,
            label + " decision is BLOCKED; resolve the blocking findings and re-review",
        )
    elif decision in ("PASS", "PASS_WITH_WARNINGS") and unresolved_blocking:
        report.error(
            "GATE-" + code + "-FABRICATED-PASS",
            path,
            label
            + " decision is "
            + decision
            + " with "
            + str(unresolved_blocking)
            + " unresolved BLOCKING finding(s); a blocking finding cannot pass the gate",
        )
    return decision


def check_adversarial_review(
    report: Report, repo: Path, change_dir: Path, human_approved: bool
) -> None:
    """Validate the adversarial review record: structure, findings, decision."""
    path = change_dir / "adversarial-review.md"
    if not path.is_file():
        report.check("adversarial review", "fail", "record missing")
        return
    text = path.read_text(encoding="utf-8", errors="replace")
    sections = {}
    for title in ADVERSARIAL_SECTIONS:
        sections[title] = find_section(report, path, text, title)
    if sections["Review Findings" if False else "Findings"] is None:
        report.check("adversarial review", "fail", "record incomplete")
        return

    record = parse_fields(sections["Review Record"] or "")
    one_field(report, "GATE-AR-FIELD", path, record, "change", "Change", strict=False)
    enum_field(
        report,
        "GATE-AR-TYPE",
        path,
        record,
        "review type",
        "Review type",
        ("ADVERSARIAL_REVIEW",),
    )
    reviewer = one_field(
        report, "GATE-AR-REVIEWER", path, record, "reviewer", "Reviewer (agent/session and role)"
    )
    author = one_field(report, "GATE-AR-AUTHOR", path, record, "author", "Author context")
    mechanism = enum_field(
        report,
        "GATE-AR-INDEPENDENCE",
        path,
        record,
        "independence mechanism",
        "Independence mechanism",
        INDEPENDENCE,
    )
    if mechanism == "NONE":
        reason = one_field(
            report,
            "GATE-AR-INDEPENDENCE-REASON",
            path,
            record,
            "independence exception reason",
            "Independence exception reason",
        )
        waiver = one_field(
            report,
            "GATE-AR-INDEPENDENCE-WAIVER",
            path,
            record,
            "independence waiver",
            "Independence waiver (human decision reference)",
        )
        if waiver is not None:
            resolve_approval_reference(report, repo, path, waiver, prefix="AR-WAIVER")
        if reason is not None and waiver is not None:
            report.warn(
                "GATE-AR-INDEPENDENCE-WEAK",
                path,
                "adversarial review ran without a separate reviewer context; human waiver "
                + repr(waiver)
                + " recorded; reason: "
                + reason,
            )
    if reviewer and author and normalize_identity(reviewer) == normalize_identity(author):
        report.error(
            "GATE-AR-SELF-REVIEW",
            path,
            "reviewer and author contexts are the same ("
            + repr(reviewer)
            + "); an adversarial review must come from a context that did not write the artifacts",
        )
    one_field(report, "GATE-AR-ARTIFACTS", path, record, "artifacts reviewed", "Artifacts reviewed")
    reviewed_at = one_field(
        report, "GATE-AR-TIME", path, record, "reviewed at", "Reviewed at (UTC)", strict=False
    )
    if reviewed_at and not ISO_DATE_RE.search(reviewed_at):
        report.error("GATE-AR-TIME", path, "Reviewed at is not an ISO date: " + repr(reviewed_at))

    scope_pairs = parse_fields(sections["Review Scope"] or "")
    for area in ADVERSARIAL_SCOPE:
        values = field_values(scope_pairs, area)
        if not values:
            report.error("GATE-AR-SCOPE", path, "review scope has no entry for '" + area + "'")
            continue
        check_disposition(report, "GATE-AR-SCOPE", path, area, values[0])

    for title in (
        "Assumption Challenges",
        "Requirement Gaps",
        "Design Counterexamples",
        "Acceptance Criteria Weaknesses",
    ):
        body = re.sub(r"<!--.*?-->", "", sections[title] or "", flags=re.DOTALL).strip()
        if is_placeholder(body, strict=False):
            report.error("GATE-AR-EMPTY-SECTION", path, "'## " + title + "' has no content")

    scientific = parse_fields(sections["Scientific Validity"] or "")
    for area in (
        "Evidence applicability",
        "Biological assumptions",
        "Parameter provenance",
        "Mathematical assumptions",
        "Model limitations",
        "Falsifiability",
        "Uncertainty",
    ):
        values = field_values(scientific, area)
        if not values:
            report.error(
                "GATE-AR-SCIENTIFIC", path, "Scientific Validity has no entry for '" + area + "'"
            )
        elif is_placeholder(values[0], strict=False):
            report.error(
                "GATE-AR-SCIENTIFIC", path, "Scientific Validity entry '" + area + "' is empty"
            )

    rows, unresolved_blocking, accepted_blocking = check_findings_table(
        report,
        path,
        sections["Findings"] or "",
        "Findings",
        "Evidence or reasoning",
        "Proposed resolution",
    )
    if accepted_blocking and not human_approved:
        report.error(
            "GATE-AR-WAIVER-APPROVAL",
            path,
            "a BLOCKING finding is closed as ACCEPTED_RISK, which needs a"
            " recorded human approval in verification/acceptance.md",
        )

    decision_body = sections["Review Decision"] or ""
    decision = check_review_decision(
        report, "AR", path, decision_body, "adversarial review", unresolved_blocking
    )
    decision_pairs = parse_fields(decision_body)
    one_field(
        report,
        "GATE-AR-BASIS",
        path,
        decision_pairs,
        "basis for the decision",
        "Basis for the decision",
        strict=False,
    )
    if decision is not None:
        one_field(
            report,
            "GATE-AR-RESOLUTIONS",
            path,
            decision_pairs,
            "required resolutions before tasks.md",
            "Required resolutions before tasks.md",
            strict=False,
        )
        if decision == "PASS_WITH_WARNINGS" and not [
            row for row in rows if row["status"] != "RESOLVED"
        ]:
            report.warn(
                "GATE-AR-WARNINGS",
                path,
                "decision is PASS_WITH_WARNINGS but every finding is RESOLVED",
            )
    status = (
        "fail"
        if any(issue.path == str(path) and issue.severity == "error" for issue in report.issues)
        else "ok"
    )
    report.check(
        "adversarial review",
        status,
        (decision or "no decision")
        + ", "
        + str(len(rows))
        + " finding(s), "
        + str(unresolved_blocking)
        + " open BLOCKING",
    )


# --------------------------------------------------------------------------- #
# independent code review
# --------------------------------------------------------------------------- #

CODE_REVIEW_SECTIONS = (
    "Review Record",
    "Review Method",
    "Findings",
    "Follow-up Verification",
    "Review Decision",
)
CODE_REVIEW_METHOD = (
    "Actual code changes",
    "Relevant surrounding code",
    "Specifications",
    "Design decisions",
    "Tests",
    "Error handling",
    "Security implications",
    "Regression risks",
)


def check_code_review(report: Report, repo: Path, change_dir: Path, human_approved: bool) -> tuple:
    """Validate the independent code review record. Returns (implementer, decision)."""
    path = change_dir / "verification" / "code-review.md"
    if not path.is_file():
        report.error(
            "GATE-CR-MISSING",
            path,
            "independent code review record is missing; see templates/verification/code-review.md",
        )
        report.check("independent code review", "fail", "record missing")
        return None, None
    text = path.read_text(encoding="utf-8", errors="replace")
    sections = {}
    for title in CODE_REVIEW_SECTIONS:
        sections[title] = find_section(report, path, text, title)
    if any(body is None for body in sections.values()):
        report.check("independent code review", "fail", "record incomplete")
        return None, None

    record = parse_fields(sections["Review Record"] or "")
    one_field(report, "GATE-CR-FIELD", path, record, "change", "Change", strict=False)
    enum_field(
        report,
        "GATE-CR-TYPE",
        path,
        record,
        "review type",
        "Review type",
        ("INDEPENDENT_CODE_REVIEW",),
    )
    reviewer = one_field(
        report, "GATE-CR-REVIEWER", path, record, "reviewer", "Reviewer (agent/session and role)"
    )
    implementer = one_field(
        report, "GATE-CR-IMPLEMENTER", path, record, "implementer", "Implementer (agent/session)"
    )
    mechanism = enum_field(
        report,
        "GATE-CR-INDEPENDENCE",
        path,
        record,
        "independence mechanism",
        "Independence mechanism",
        INDEPENDENCE,
    )
    if mechanism == "NONE":
        reason = one_field(
            report,
            "GATE-CR-INDEPENDENCE-REASON",
            path,
            record,
            "independence exception reason",
            "Independence exception reason",
        )
        waiver = one_field(
            report,
            "GATE-CR-INDEPENDENCE-WAIVER",
            path,
            record,
            "independence waiver",
            "Independence waiver (human decision reference)",
        )
        if waiver is not None:
            resolve_approval_reference(report, repo, path, waiver, prefix="CR-WAIVER")
        if reason is not None and waiver is not None:
            report.warn(
                "GATE-CR-INDEPENDENCE-WEAK",
                path,
                "code review ran without a separate reviewer context; human waiver "
                + repr(waiver)
                + " recorded; reason: "
                + reason,
            )
    one_field(
        report,
        "GATE-CR-INDEPENDENCE-VERIFY",
        path,
        record,
        "verification of independence",
        "Verification of independence",
    )
    diff = one_field(report, "GATE-CR-DIFF", path, record, "diff reviewed", "Diff reviewed")
    if diff and not (
        PATH_LIKE_RE.search(diff)
        or re.search(r"[0-9a-f]{7,40}", diff)
        or "worktree" in normalize(diff)
    ):
        report.error(
            "GATE-CR-DIFF",
            path,
            "Diff reviewed " + repr(diff) + " names no commit, path, or worktree state",
        )
    coverage = one_field(report, "GATE-CR-COVERAGE", path, record, "coverage", "Coverage")
    if coverage is not None and not PATH_LIKE_RE.search(coverage):
        report.warn("GATE-CR-COVERAGE", path, "Coverage names no file path: " + repr(coverage))
    reviewed_at = one_field(
        report, "GATE-CR-TIME", path, record, "reviewed at", "Reviewed at (UTC)", strict=False
    )
    if reviewed_at and not ISO_DATE_RE.search(reviewed_at):
        report.error("GATE-CR-TIME", path, "Reviewed at is not an ISO date: " + repr(reviewed_at))
    if reviewer and implementer and normalize_identity(reviewer) == normalize_identity(implementer):
        report.error(
            "GATE-CR-SELF-REVIEW",
            path,
            "reviewer and implementer are the same context ("
            + repr(reviewer)
            + "); a self-review is not an independent code review",
        )

    method_pairs = parse_fields(sections["Review Method"] or "")
    for area in CODE_REVIEW_METHOD:
        values = field_values(method_pairs, area)
        if not values:
            report.error("GATE-CR-METHOD", path, "Review Method has no entry for '" + area + "'")
            continue
        check_disposition(report, "GATE-CR-METHOD", path, area, values[0])

    rows, unresolved_blocking, accepted_blocking = check_findings_table(
        report,
        path,
        sections["Findings"] or "",
        "Findings",
        "Reproduction or supporting evidence",
        "Recommended correction",
        location_token="File and location",
    )
    if accepted_blocking and not human_approved:
        report.error(
            "GATE-CR-WAIVER-APPROVAL",
            path,
            "a BLOCKING finding is closed as ACCEPTED_RISK, which needs a"
            " recorded human approval in verification/acceptance.md",
        )

    decision = check_review_decision(
        report, "CR", path, sections["Review Decision"] or "", "code review", unresolved_blocking
    )
    decision_pairs = parse_fields(sections["Review Decision"] or "")
    one_field(
        report,
        "GATE-CR-BASIS",
        path,
        decision_pairs,
        "basis for the decision",
        "Basis for the decision",
        strict=False,
    )
    one_field(
        report,
        "GATE-CR-RISK",
        path,
        decision_pairs,
        "residual risk accepted",
        "Residual risk accepted",
        strict=False,
    )

    follow_up = sections["Follow-up Verification"] or ""
    resolved = [row for row in rows if row["status"] == "RESOLVED"]
    if resolved:
        table = require_table(
            report,
            "GATE-CR-FOLLOWUP",
            path,
            follow_up,
            "Follow-up Verification",
            ["Finding ID", "Re-verification command or check", "Result"],
        )
        if table is not None:
            for row in resolved:
                matching = [
                    candidate
                    for candidate in table["rows"]
                    if normalize(cell(candidate, table, "finding id")) == normalize(row["id"])
                ]
                if not matching:
                    report.error(
                        "GATE-CR-FOLLOWUP",
                        path,
                        row["id"]
                        + " is RESOLVED with no Follow-up Verification row recording the re-check",
                    )
                    continue
                entry = matching[0]
                if is_placeholder(
                    cell(entry, table, "re-verification command or check"), strict=False
                ):
                    report.error(
                        "GATE-CR-FOLLOWUP",
                        path,
                        row["id"] + " follow-up names no re-verification check",
                    )
                if is_placeholder(cell(entry, table, "result"), strict=False):
                    report.error(
                        "GATE-CR-FOLLOWUP", path, row["id"] + " follow-up records no result"
                    )
    status = (
        "fail"
        if any(issue.path == str(path) and issue.severity == "error" for issue in report.issues)
        else "ok"
    )
    report.check(
        "independent code review",
        status,
        (decision or "no decision")
        + ", "
        + str(len(rows))
        + " finding(s), "
        + str(unresolved_blocking)
        + " open BLOCKING",
    )
    return implementer, decision


# --------------------------------------------------------------------------- #
# traceability
# --------------------------------------------------------------------------- #


def check_execution_evidence(report: Report, path, body: str) -> dict:
    """Validate the execution-evidence table; return command -> exit code."""
    table = require_table(
        report,
        "GATE-TR-EXEC-COLUMNS",
        path,
        body,
        "Execution Evidence",
        ["Command", "Exit code", "Result summary", "Recorded by"],
    )
    if table is None:
        return {}
    commands = {}
    for row in table["rows"]:
        command = cell(row, table, "command")
        exit_raw = cell(row, table, "exit code")
        summary = cell(row, table, "result summary")
        recorder = cell(row, table, "recorded by")
        if is_placeholder(command.strip(BACKTICK), strict=False):
            report.error("GATE-TR-EXEC-COMMAND", path, "execution evidence row has no command")
            continue
        if not re.fullmatch(r"\d+", exit_raw.strip()):
            report.error(
                "GATE-TR-EXEC-EXIT",
                path,
                "command " + repr(command) + " has no numeric exit code: " + repr(exit_raw),
            )
        if is_placeholder(summary, strict=False):
            report.error(
                "GATE-TR-EXEC-RESULT",
                path,
                "command " + repr(command) + " records no result summary",
            )
        if is_placeholder(recorder, strict=True):
            report.error(
                "GATE-TR-EXEC-RECORDER", path, "command " + repr(command) + " records no recorder"
            )
        code = int(exit_raw) if exit_raw.strip().isdigit() else None
        if code not in (None, 0):
            if "expected" in normalize(summary):
                report.warn(
                    "GATE-TR-EXEC-FAIL",
                    path,
                    "command "
                    + repr(command)
                    + " exited "
                    + str(code)
                    + " and is recorded as an expected failure",
                )
            else:
                report.error(
                    "GATE-TR-EXEC-FAIL",
                    path,
                    "command "
                    + repr(command)
                    + " exited "
                    + str(code)
                    + "; fix it or record it as an expected failure in the result summary",
                )
        commands[command.strip(BACKTICK).strip()] = code
    if not commands:
        report.error("GATE-TR-EXEC-EMPTY", path, "execution evidence table has no usable row")
    return commands


def check_unplanned(report: Report, path, body: str, implementer) -> None:
    """Require unplanned behavior to be either absent-and-stated or reviewed."""
    stripped = re.sub(r"<!--.*?-->", "", body, flags=re.DOTALL)
    tables = parse_tables(stripped)
    rows = tables[0]["rows"] if tables else []
    if not rows:
        if not any(NONE_LINE_RE.match(line) for line in stripped.splitlines()):
            report.error(
                "GATE-TR-UNPLANNED",
                path,
                "state 'None.' when nothing unplanned shipped, or record the"
                " deviations in the table",
            )
        return
    table = tables[0]
    for row in rows:
        deviation_id = cell(row, table, "deviation id")
        if is_placeholder(deviation_id, strict=False):
            report.error("GATE-TR-UNPLANNED-ID", path, "deviation row has no identifier")
            continue
        for token in ("description", "spec impact", "reviewed by", "decision"):
            if is_placeholder(cell(row, table, token), strict=False):
                report.error("GATE-TR-UNPLANNED", path, deviation_id + " has no '" + token + "'")
        reviewer = cell(row, table, "reviewed by")
        if (
            implementer
            and reviewer
            and normalize_identity(reviewer) == normalize_identity(implementer)
        ):
            report.error(
                "GATE-TR-UNPLANNED-SELF", path, deviation_id + " is reviewed by its own implementer"
            )


def resolve_evidence_id(repo: Path, identifier: str) -> bool:
    """Whether an evidence identifier appears in a record under docs/evidence/."""
    evidence_dir = repo / EVIDENCE_REL
    if not evidence_dir.is_dir():
        return False
    wanted = identifier.strip().strip(BACKTICK).lower()
    for candidate in evidence_dir.rglob("*.md"):
        if "templates" in candidate.relative_to(evidence_dir).parts:
            continue
        if wanted in candidate.read_text(encoding="utf-8", errors="replace").lower():
            return True
    return False


def check_scientific_traceability(
    report: Report, repo: Path, path, body: str, commands: dict
) -> dict:
    """Validate the scientific chain and evidence resolution. Returns counts by status."""
    table = require_table(
        report,
        "GATE-TR-SCI-COLUMNS",
        path,
        body,
        "Scientific Traceability",
        [
            "Evidence ID",
            "Scientific Assumption",
            "Parameter ID",
            "Mathematical Model",
            "Validation Evidence",
            "Data class",
            "Status",
        ],
    )
    if table is None:
        return {}
    counts: dict = {}
    for row in table["rows"]:
        evidence_id = cell(row, table, "evidence id")
        data_class = enum_value(
            report,
            "GATE-TR-DATA-CLASS",
            path,
            cell(row, table, "data class"),
            DATA_CLASSES,
            "Data class",
        )
        status = enum_value(
            report,
            "GATE-TR-SCI-STATUS",
            path,
            cell(row, table, "status"),
            TRACE_STATUSES,
            "Scientific traceability status",
        )
        if status:
            counts[status] = counts.get(status, 0) + 1
        if status in ("VERIFIED", "PARTIALLY_VERIFIED"):
            if is_placeholder(evidence_id, strict=True):
                report.error(
                    "GATE-TR-EVIDENCE-ID",
                    path,
                    "a " + str(status) + " scientific row names no evidence ID",
                )
            else:
                for token in re.split(r"[,\s]+", evidence_id.strip(BACKTICK)):
                    if not token or token.lower() in ("none", "n/a", "unknown"):
                        continue
                    if not resolve_evidence_id(repo, token):
                        report.error(
                            "GATE-TR-EVIDENCE-UNRESOLVED",
                            path,
                            "evidence ID " + repr(token) + " has no record under docs/evidence/",
                        )
        if data_class == "UNVERIFIED" and status == "VERIFIED":
            report.error(
                "GATE-TR-UNKNOWN-CLOSED",
                path,
                "a row with Data class UNVERIFIED cannot be VERIFIED",
            )
        if data_class == "SIMULATED":
            haystack = normalize(" ".join(str(value) for value in row.values()))
            for phrase in SIMULATED_FORBIDDEN_PHRASES:
                if phrase in haystack:
                    report.error(
                        "GATE-TR-SIMULATED-AS-OBSERVED",
                        path,
                        "row (Data class SIMULATED) describes "
                        + repr(phrase)
                        + "; simulated output is not an observation",
                    )
        if status == "VERIFIED":
            for token in (
                "scientific assumption",
                "parameter id",
                "mathematical model",
                "validation evidence",
            ):
                if is_placeholder(cell(row, table, token), strict=False):
                    report.error(
                        "GATE-TR-SCI-FIELD",
                        path,
                        "a VERIFIED scientific row has no '" + token + "'",
                    )
            validation = cell(row, table, "validation evidence")
            cited = commands_in(validation)
            if cited:
                for command in cited:
                    if command not in commands:
                        report.error(
                            "GATE-TR-SCI-EVIDENCE",
                            path,
                            "validation evidence cites "
                            + repr(command)
                            + ", which is not in the Execution Evidence table",
                        )
            elif not PATH_LIKE_RE.search(validation):
                report.error(
                    "GATE-TR-SCI-EVIDENCE",
                    path,
                    "validation evidence "
                    + repr(validation)
                    + " cites no recorded command and no docs/ path",
                )
        if status in ("PARTIALLY_VERIFIED", "NOT_APPLICABLE"):
            gaps = cell(row, table, "residual gaps")
            if is_placeholder(gaps, strict=False):
                report.error(
                    "GATE-TR-GAPS",
                    path,
                    "a " + str(status) + " row records no reason in 'Residual gaps'",
                )
    return counts


def check_traceability(
    report: Report, repo: Path, change_dir: Path, requirements: dict, implementer
) -> None:
    """Validate the traceability report: coverage, evidence, decisions."""
    path = change_dir / "verification" / "traceability.md"
    if not path.is_file():
        report.error(
            "GATE-TR-MISSING",
            path,
            "traceability report is missing; see templates/verification/traceability.md",
        )
        report.check("traceability validation", "fail", "report missing")
        return
    text = path.read_text(encoding="utf-8", errors="replace")
    record_body = find_section(report, path, text, "Traceability Record")
    exec_body = find_section(report, path, text, "Execution Evidence")
    engineering_body = find_section(report, path, text, "Engineering Traceability")
    unplanned_body = find_section(report, path, text, "Unplanned or Deviations")
    qa_body = find_section(report, path, text, "QA and Model Validation")
    sci_body = find_section(report, path, text, "Scientific Traceability")
    decision_body = find_section(report, path, text, "Traceability Decision")
    if any(
        body is None
        for body in (
            record_body,
            exec_body,
            engineering_body,
            unplanned_body,
            qa_body,
            decision_body,
        )
    ):
        report.check("traceability validation", "fail", "report incomplete")
        return

    record = parse_fields(record_body or "")
    one_field(report, "GATE-TR-FIELD", path, record, "change", "Change", strict=False)
    reviewer = one_field(
        report, "GATE-TR-REVIEWER", path, record, "traceability reviewer", "Traceability reviewer"
    )
    mechanism = enum_field(
        report,
        "GATE-TR-INDEPENDENCE",
        path,
        record,
        "independence mechanism",
        "Independence mechanism",
        INDEPENDENCE,
    )
    if mechanism == "NONE":
        reason = one_field(
            report,
            "GATE-TR-INDEPENDENCE-REASON",
            path,
            record,
            "independence exception reason",
            "Independence exception reason",
        )
        if reason is not None:
            report.warn(
                "GATE-TR-INDEPENDENCE-WEAK",
                path,
                "traceability was validated without a separate context; reason: " + reason,
            )
    verified_at = one_field(
        report, "GATE-TR-TIME", path, record, "verified at", "Verified at (UTC)", strict=False
    )
    if verified_at and not ISO_DATE_RE.search(verified_at):
        report.error("GATE-TR-TIME", path, "Verified at is not an ISO date: " + repr(verified_at))
    if reviewer and implementer and normalize_identity(reviewer) == normalize_identity(implementer):
        report.error(
            "GATE-TR-SELF-VALIDATION",
            path,
            "traceability reviewer is the implementer ("
            + repr(reviewer)
            + "); traceability must be validated independently",
        )
    applicability = enum_field(
        report,
        "GATE-TR-APPLICABILITY",
        path,
        record,
        "scientific traceability applicability",
        "Scientific Traceability Applicability",
        ("APPLICABLE", "NOT_APPLICABLE"),
    )
    if applicability == "NOT_APPLICABLE":
        one_field(
            report,
            "GATE-TR-APPLICABILITY-REASON",
            path,
            record,
            "non-applicability reason",
            "Non-applicability reason",
        )

    commands = check_execution_evidence(report, path, exec_body or "")

    table = require_table(
        report,
        "GATE-TR-ENG-COLUMNS",
        path,
        engineering_body or "",
        "Engineering Traceability",
        [
            "Requirement ID",
            "Acceptance Criteria / Scenario",
            "Implementation",
            "Tests",
            "Execution Evidence",
            "Status",
            "Residual gaps",
        ],
    )
    counts: dict = {}
    seen: dict = {}
    if table is not None:
        for row in table["rows"]:
            identifier = normalize(cell(row, table, "requirement id"))
            if not identifier:
                report.error(
                    "GATE-TR-ROW-ID", path, "an engineering traceability row has no requirement ID"
                )
                continue
            if identifier in seen:
                report.error(
                    "GATE-TR-ROW-DUPLICATE",
                    path,
                    cell(row, table, "requirement id")
                    + " is listed twice; keep one row per requirement",
                )
                continue
            seen[identifier] = cell(row, table, "requirement id")
            status = enum_value(
                report,
                "GATE-TR-STATUS",
                path,
                cell(row, table, "status"),
                TRACE_STATUSES,
                "Traceability status",
            )
            if status:
                counts[status] = counts.get(status, 0) + 1
            if status == "VERIFIED":
                for token in (
                    "acceptance criteria / scenario",
                    "implementation",
                    "tests",
                    "execution evidence",
                ):
                    if is_placeholder(cell(row, table, token), strict=False):
                        report.error(
                            "GATE-TR-ROW-FIELD",
                            path,
                            cell(row, table, "requirement id")
                            + " is VERIFIED with no '"
                            + token
                            + "'",
                        )
                cited = commands_in(cell(row, table, "execution evidence"))
                if not cited:
                    report.error(
                        "GATE-TR-ROW-EVIDENCE",
                        path,
                        cell(row, table, "requirement id")
                        + " is VERIFIED with no backticked execution-evidence command",
                    )
                for command in cited:
                    if command not in commands:
                        report.error(
                            "GATE-TR-ROW-EVIDENCE",
                            path,
                            cell(row, table, "requirement id")
                            + " cites "
                            + repr(command)
                            + ", which is not in the Execution Evidence table",
                        )
            if status == "UNVERIFIED":
                report.error(
                    "GATE-TR-UNVERIFIED",
                    path,
                    cell(row, table, "requirement id")
                    + " is UNVERIFIED; verify it or record NOT_APPLICABLE with a"
                    " reason, and do not mark it complete",
                )
            if status in ("PARTIALLY_VERIFIED", "NOT_APPLICABLE"):
                if is_placeholder(cell(row, table, "residual gaps"), strict=False):
                    report.error(
                        "GATE-TR-GAPS",
                        path,
                        cell(row, table, "requirement id")
                        + " is "
                        + str(status)
                        + " with no reason in 'Residual gaps'",
                    )
            acceptance = cell(row, table, "acceptance criteria / scenario")
            expected_id = None
            for candidate in requirements:
                if normalize(candidate) == identifier:
                    expected_id = candidate
                    break
            if expected_id is None:
                report.error(
                    "GATE-TR-ROW-UNKNOWN",
                    path,
                    cell(row, table, "requirement id")
                    + " does not match any requirement in the change's delta specs",
                )
                continue
            scenarios = requirements[expected_id].scenarios
            if scenarios and not any(
                normalize(scenario) in normalize(acceptance) for scenario in scenarios
            ):
                report.error(
                    "GATE-TR-ROW-SCENARIO",
                    path,
                    expected_id
                    + " names no scenario; expected at least one of: "
                    + ", ".join(scenarios),
                )
            for scenario in scenarios:
                if normalize(scenario) not in normalize(acceptance):
                    report.warn(
                        "GATE-TR-ROW-SCENARIO",
                        path,
                        expected_id + " does not name scenario " + scenario,
                    )
    missing = [identifier for identifier in requirements if normalize(identifier) not in seen]
    if missing:
        preview = ", ".join(missing[:5]) + (" ..." if len(missing) > 5 else "")
        report.error(
            "GATE-TR-COVERAGE",
            path,
            str(len(missing))
            + " requirement(s) from the delta specs have no traceability row: "
            + preview,
        )

    check_unplanned(report, path, unplanned_body or "", implementer)

    qa = parse_fields(qa_body or "")
    one_field(report, "GATE-TR-QA-OWNER", path, qa, "qa owner", "QA owner")
    suites = one_field(
        report, "GATE-TR-QA-SUITES", path, qa, "test suites executed", "Test suites executed"
    )
    if suites is not None:
        cited = commands_in(suites)
        if not cited:
            report.error(
                "GATE-TR-QA-SUITES",
                path,
                "Test suites executed cites no backticked command: " + repr(suites),
            )
        for command in cited:
            if command not in commands:
                report.error(
                    "GATE-TR-QA-SUITES",
                    path,
                    "test suite "
                    + repr(command)
                    + " is not recorded in the Execution Evidence table",
                )
    model_validation = one_field(
        report,
        "GATE-TR-MODEL-VALIDATION",
        path,
        qa,
        "scientific model validation",
        "Scientific model validation",
        strict=False,
    )
    if applicability == "APPLICABLE":
        if model_validation is None or normalize(model_validation).startswith("not applicable"):
            report.error(
                "GATE-TR-MODEL-VALIDATION",
                path,
                "scientific traceability is APPLICABLE but no validation record is named",
            )
        elif PATH_LIKE_RE.search(model_validation) and not any(
            (repo / token).exists()
            for token in re.findall(
                r"[A-Za-z0-9_./-]+\.(?:md|json|toml|yaml|yml)", model_validation
            )
        ):
            report.error(
                "GATE-TR-MODEL-VALIDATION",
                path,
                "validation record path does not exist: " + repr(model_validation),
            )
    elif model_validation is not None and not normalize(model_validation).startswith(
        "not applicable"
    ):
        report.warn(
            "GATE-TR-MODEL-VALIDATION",
            path,
            "scientific traceability is NOT_APPLICABLE but a validation record is named",
        )

    if applicability == "APPLICABLE":
        if sci_body is None or not sci_body.strip():
            report.error(
                "GATE-TR-SCI-MISSING",
                path,
                "scientific traceability is APPLICABLE but '## Scientific Traceability' is empty",
            )
        else:
            check_scientific_traceability(report, repo, path, sci_body, commands)
    else:
        report.check("scientific traceability", "skip", "declared NOT_APPLICABLE")

    decision_pairs = parse_fields(decision_body or "")
    decision = enum_field(
        report,
        "GATE-TR-DECISION",
        path,
        decision_pairs,
        "decision",
        "Traceability decision",
        TRACE_STATUSES,
    )
    unverified = counts.get("UNVERIFIED", 0)
    reported = one_field(
        report,
        "GATE-TR-UNVERIFIED-COUNT",
        path,
        decision_pairs,
        "unverified requirements remaining",
        "Unverified requirements remaining",
        strict=False,
    )
    if reported is not None:
        match = re.search(r"\d+", reported)
        if not match:
            report.error(
                "GATE-TR-UNVERIFIED-COUNT",
                path,
                "Unverified requirements remaining is not an integer: " + repr(reported),
            )
        elif int(match.group(0)) != unverified:
            report.error(
                "GATE-TR-UNVERIFIED-COUNT",
                path,
                "Unverified requirements remaining says "
                + match.group(0)
                + " but the report has "
                + str(unverified)
                + " UNVERIFIED row(s)",
            )
    one_field(
        report,
        "GATE-TR-DECISION-BASIS",
        path,
        decision_pairs,
        "basis for the decision",
        "Basis for the decision",
        strict=False,
    )
    if decision == "UNVERIFIED":
        report.error(
            "GATE-TR-DECISION",
            path,
            "traceability decision is UNVERIFIED; the change is not ready to archive",
        )
    elif decision == "VERIFIED" and (counts.get("PARTIALLY_VERIFIED", 0) or unverified):
        report.error(
            "GATE-TR-DECISION-INCONSISTENT",
            path,
            "traceability decision is VERIFIED but the report has"
            " PARTIALLY_VERIFIED or UNVERIFIED rows",
        )
    elif decision == "NOT_APPLICABLE" and any(
        count and status != "NOT_APPLICABLE" for status, count in counts.items()
    ):
        report.error(
            "GATE-TR-DECISION-INCONSISTENT",
            path,
            "traceability decision is NOT_APPLICABLE but engineering rows are traced",
        )
    status = (
        "fail"
        if any(issue.path == str(path) and issue.severity == "error" for issue in report.issues)
        else "ok"
    )
    report.check(
        "traceability validation",
        status,
        (decision or "no decision")
        + ", "
        + str(len(seen))
        + "/"
        + str(len(requirements))
        + " requirement(s) mapped"
        + (", scientific " + applicability if applicability else ""),
    )


# --------------------------------------------------------------------------- #
# human acceptance
# --------------------------------------------------------------------------- #


def check_acceptance(report: Report, repo: Path, change_dir: Path) -> bool:
    """Validate the acceptance record. Returns whether a human approval is recorded."""
    path = change_dir / "verification" / "acceptance.md"
    if not path.is_file():
        report.error(
            "GATE-AC-MISSING",
            path,
            "acceptance record is missing; see templates/verification/acceptance.md",
        )
        report.check("human acceptance", "fail", "record missing")
        return False
    text = path.read_text(encoding="utf-8", errors="replace")
    body = find_section(report, path, text, "Acceptance Record")
    if body is None:
        report.check("human acceptance", "fail", "record incomplete")
        return False
    pairs = parse_fields(body)
    one_field(report, "GATE-AC-FIELD", path, pairs, "change", "Change", strict=False)
    required = enum_field(
        report,
        "GATE-AC-REQUIRED",
        path,
        pairs,
        "human acceptance required",
        "Human Acceptance Required",
        ("YES", "NO"),
    )
    trigger = enum_field(
        report, "GATE-AC-TRIGGER", path, pairs, "required per", "Required per", ACCEPTANCE_TRIGGERS
    )
    consensus = one_field(
        report,
        "GATE-AC-CONSENSUS",
        path,
        pairs,
        "agent consensus used as approval",
        "Agent consensus used as approval",
        strict=False,
    )
    if consensus is not None and normalize(consensus) not in ("no", "false", "none"):
        report.error(
            "GATE-AC-CONSENSUS",
            path,
            "agent consensus is recorded as approval ("
            + repr(consensus)
            + "); only a human decision counts as approval",
        )
    decision = enum_field(
        report, "GATE-AC-DECISION", path, pairs, "decision", "Decision", ACCEPTANCE_DECISIONS
    )
    approved = False
    if required == "NO":
        if trigger is not None and trigger != "NONE":
            report.error(
                "GATE-AC-TRIGGER-CONFLICT",
                path,
                "Human Acceptance Required is NO but Required per is "
                + trigger
                + "; record the approval or correct the trigger",
            )
        one_field(
            report,
            "GATE-AC-REASON",
            path,
            pairs,
            "non-applicability reason",
            "Non-applicability reason",
        )
    elif required == "YES":
        approver = one_field(
            report,
            "GATE-AC-APPROVER",
            path,
            pairs,
            "approver",
            "Approver (human identity and role)",
        )
        reference = one_field(
            report, "GATE-AC-REFERENCE", path, pairs, "approval reference", "Approval reference"
        )
        approved_at = one_field(
            report, "GATE-AC-TIME", path, pairs, "approved at", "Approved at (UTC)", strict=False
        )
        one_field(report, "GATE-AC-SCOPE", path, pairs, "scope of approval", "Scope of approval")
        if approved_at and not ISO_DATE_RE.search(approved_at):
            report.error(
                "GATE-AC-TIME", path, "Approved at is not an ISO date: " + repr(approved_at)
            )
        if reference is not None:
            resolve_approval_reference(report, repo, path, reference)
        if decision != "APPROVED":
            report.error(
                "GATE-AC-NOT-APPROVED",
                path,
                "human acceptance is required but the recorded decision is "
                + str(decision)
                + "; archive stays blocked",
            )
        elif approver and reference:
            approved = True
    if decision == "APPROVED" and required == "NO":
        report.warn(
            "GATE-AC-UNREQUIRED",
            path,
            "an approval is recorded although Human Acceptance Required is NO",
        )
    report.check(
        "human acceptance",
        "ok" if approved else ("skip" if required == "NO" else "fail"),
        "required: " + str(required),
    )
    return approved


def resolve_approval_reference(
    report: Report, repo: Path, path, reference: str, prefix: str = "AC"
) -> None:
    """An approval reference must be an existing record or an opaque external id.

    The scheme of an external id is chosen by whoever recorded the decision, so
    no scheme is privileged and none is required: any '<scheme>:<id>' or
    '<scheme>#<id>' token is accepted as unverifiable provenance.
    """
    relative = reference.strip().strip(BACKTICK)
    if re.fullmatch(r"[A-Za-z][A-Za-z0-9_.-]*[:#][A-Za-z0-9._:/-]+", relative):
        report.warn(
            "GATE-" + prefix + "-REFERENCE-EXTERNAL",
            path,
            "approval reference "
            + repr(relative)
            + " is an external id this gate cannot verify; keep the transcript"
            " or decision record reachable",
        )
        return
    candidate = repo / relative
    if candidate.exists():
        return
    matches = re.findall(r"[A-Za-z0-9_./-]+\.(?:md|json|toml|yaml|yml|txt|log)", reference)
    if matches and any((repo / match).exists() for match in matches):
        return
    report.error(
        "GATE-" + prefix + "-REFERENCE",
        path,
        "approval reference "
        + repr(reference)
        + " resolves to no file in the repository and no external decision id",
    )


# --------------------------------------------------------------------------- #
# OpenSpec CLI
# --------------------------------------------------------------------------- #


def find_openspec() -> str | None:
    override = os.environ.get("RATSIGHT_OPENSPEC_BIN")
    if override:
        return override
    return shutil.which("openspec")


def run_cli(command: list, repo: Path, timeout: int = 240) -> tuple:
    """Run the OpenSpec CLI. Returns (returncode, output); -1 when unavailable."""
    try:
        completed = subprocess.run(
            command,
            cwd=str(repo),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except (
        OSError,
        subprocess.SubprocessError,
    ) as error:  # pragma: no cover - environment dependent
        return -1, str(error)
    return completed.returncode, (completed.stdout or "") + (completed.stderr or "")


def check_openspec_cli(report: Report, repo: Path, change: str, skip: bool) -> None:
    """Final OpenSpec verification: change validation, schema validation, status."""
    if skip:
        report.warn(
            "GATE-OPENSPEC-SKIPPED",
            repo / SCHEMA_REL,
            "--skip-openspec given: change validation, schema validation, and"
            " CLI artifact status were not run",
        )
        report.check("openspec verification", "skip", "--skip-openspec")
        return
    binary = find_openspec()
    if not binary:
        report.error(
            "GATE-OPENSPEC-MISSING",
            repo / SCHEMA_REL,
            "openspec CLI not found; install it or set RATSIGHT_OPENSPEC_BIN"
            " (or pass --skip-openspec, which is recorded as a limitation)",
        )
        report.check("openspec verification", "fail", "CLI not found")
        return
    failures = []
    code, output = run_cli([binary, "validate", change], repo)
    if code != 0:
        failures.append("openspec validate " + change + " failed:\n" + indent_tail(output))
    strict_code, strict_output = run_cli([binary, "validate", change, "--strict"], repo)
    if strict_code != 0:
        report.warn(
            "GATE-OPENSPEC-STRICT",
            repo / CHANGES_REL / change,
            "openspec validate --strict reports issues (not fatal for this gate):\n"
            + indent_tail(strict_output),
        )
    schema_code, schema_output = run_cli([binary, "schema", "validate", SCHEMA_NAME], repo)
    if schema_code != 0:
        failures.append(
            "openspec schema validate " + SCHEMA_NAME + " failed:\n" + indent_tail(schema_output)
        )
    status_code, status_output = run_cli([binary, "status", "--change", change, "--json"], repo)
    if status_code != 0:
        failures.append(
            "openspec status --change " + change + " failed:\n" + indent_tail(status_output)
        )
    else:
        failures.extend(check_artifact_status(status_output))
    for failure in failures:
        report.error("GATE-OPENSPEC", repo / CHANGES_REL / change, failure)
    report.check(
        "openspec verification", "fail" if failures else "ok", str(len(failures)) + " failure(s)"
    )


def check_artifact_status(status_output: str) -> list:
    """Read the CLI's own view of which planning artifacts exist."""
    try:
        payload = json.loads(status_output)
    except ValueError:
        return ["openspec status did not return JSON; cannot confirm artifact completion"]
    failures = []
    paths = payload.get("artifactPaths") or {}
    if "adversarial-review" not in paths:
        failures.append(
            "the OpenSpec CLI does not list the adversarial-review artifact for"
            " this change; check openspec/config.yaml schema selection"
        )
    for artifact_id, entry in paths.items():
        existing = (entry or {}).get("existingOutputPaths") or []
        if not existing:
            failures.append(
                "planning artifact '"
                + artifact_id
                + "' is not created according to the OpenSpec CLI"
            )
    if payload.get("isPlanningComplete") is False and not failures:
        failures.append("OpenSpec reports planning is incomplete")
    return failures


def indent_tail(output: str, lines: int = 6) -> str:
    tail = [line for line in (output or "").strip().splitlines() if line.strip()][-lines:]
    return "\n".join("    " + line for line in tail) if tail else "    (no output)"


# --------------------------------------------------------------------------- #
# entry point
# --------------------------------------------------------------------------- #


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="openspec_quality_gate.py",
        description="Deterministic, evidence-based quality gate for RatSight OpenSpec changes.",
    )
    parser.add_argument(
        "change",
        nargs="?",
        help="change name under openspec/changes/ (default: the single active change)",
    )
    parser.add_argument(
        "--repo-root",
        default=None,
        help="repository root (default: nearest directory containing openspec/)",
    )
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    parser.add_argument(
        "--allow-no-change", action="store_true", help="exit 0 when no active change exists"
    )
    parser.add_argument(
        "--skip-openspec",
        action="store_true",
        help="skip OpenSpec CLI validation (recorded as a limitation in the output)",
    )
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    repo = Path(args.repo_root).resolve() if args.repo_root else resolve_repo_root(Path.cwd())
    if repo is None:
        print("quality gate: no openspec/ directory found from " + str(Path.cwd()), file=sys.stderr)
        return EXIT_USAGE
    changes = active_changes(repo)
    change = args.change
    if change is None:
        if not changes:
            message = "quality gate: no active change under " + str(repo / CHANGES_REL)
            if args.allow_no_change:
                print(message + " - nothing to gate")
                return EXIT_PASS
            print(message + "; pass a change name or --allow-no-change", file=sys.stderr)
            return EXIT_USAGE
        if len(changes) > 1:
            print(
                "quality gate: multiple active changes (" + ", ".join(changes) + "); name one",
                file=sys.stderr,
            )
            return EXIT_USAGE
        change = changes[0]
    change_dir = repo / CHANGES_REL / change
    if not change_dir.is_dir():
        print("quality gate: no such change: " + str(change_dir), file=sys.stderr)
        return EXIT_USAGE

    report = Report(repo=repo, change=change)
    check_schema(report, repo)
    check_planning_artifacts(report, change_dir)
    check_tasks_complete(report, change_dir)
    requirements = collect_requirements(report, change_dir)
    approved = check_acceptance(report, repo, change_dir)
    check_adversarial_review(report, repo, change_dir, approved)
    implementer, _decision = check_code_review(report, repo, change_dir, approved)
    check_traceability(report, repo, change_dir, requirements, implementer)
    check_openspec_cli(report, repo, change, args.skip_openspec)

    emit(report, as_json=args.json)
    return EXIT_PASS if report.passed else EXIT_BLOCKED


def emit(report: Report, as_json: bool = False) -> None:
    payload = {
        "change": report.change,
        "repo": str(report.repo),
        "schema": SCHEMA_NAME,
        "passed": report.passed,
        "checks": [
            {"name": check.name, "status": check.status, "detail": check.detail}
            for check in report.checks
        ],
        "errors": [
            {"code": issue.code, "path": issue.path, "message": issue.message}
            for issue in report.errors
        ],
        "warnings": [
            {"code": issue.code, "path": issue.path, "message": issue.message}
            for issue in report.warnings
        ],
        "note": (
            "checks recorded evidence for completeness and consistency;"
            " it does not verify that a review happened"
        ),
    }
    if as_json:
        print(json.dumps(payload, indent=2))
        return
    print("RatSight OpenSpec quality gate")
    print("  change: " + report.change)
    print("  repo:   " + str(report.repo))
    print("  schema: " + SCHEMA_NAME + " (openspec/schemas/" + SCHEMA_NAME + "/schema.yaml)")
    print()
    print("checks:")
    for check in report.checks:
        detail = " - " + check.detail if check.detail else ""
        print("  [" + check.status + "] " + check.name + detail)
    for title, issues in (("errors", report.errors), ("warnings", report.warnings)):
        if not issues:
            continue
        print()
        print(title + " (" + str(len(issues)) + "):")
        for issue in issues:
            print("  " + issue.code)
            print("    " + issue.path)
            for line in issue.message.splitlines():
                print("    " + line)
    print()
    if report.passed:
        print("RESULT: PASS (" + str(len(report.warnings)) + " warning(s))")
        print("This gate checked recorded evidence only; it is not an independent review.")
    else:
        print(
            "RESULT: BLOCKED ("
            + str(len(report.errors))
            + " error(s), "
            + str(len(report.warnings))
            + " warning(s))"
        )
        print("Fix the records and the work they describe, then re-run. Do not weaken the gate.")
        print("Templates: openspec/schemas/" + SCHEMA_NAME + "/templates/")


if __name__ == "__main__":
    sys.exit(main())
