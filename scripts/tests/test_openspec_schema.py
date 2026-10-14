"""Compatibility tests for the project-local evidence-driven OpenSpec schema.

These tests hold the schema to the installed CLI: the artifact graph, the
supported schema keys, the templates the artifacts point at, and the CLI's own
view of the schema. They also pin the requirement/scenario Markdown format the
CLI validates, so a template change cannot quietly break validation.

Tests that need the real CLI skip when it is absent, so the suite stays usable
offline. They never touch the repository's openspec tree: every CLI test
scaffolds a throwaway OpenSpec root under pytest's tmp_path.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIR = REPO_ROOT / "openspec" / "schemas" / "evidence-driven"
SCHEMA_FILE = SCHEMA_DIR / "schema.yaml"
TEMPLATES = SCHEMA_DIR / "templates"

ARTIFACT_ORDER = ["proposal", "specs", "design", "adversarial-review", "tasks"]
TOP_LEVEL_KEYS = {"name", "version", "description", "artifacts", "apply"}
ARTIFACT_KEYS = {"id", "generates", "description", "template", "instruction", "requires"}

CLI = os.environ.get("RATSIGHT_OPENSPEC_BIN") or shutil.which("openspec")
needs_cli = pytest.mark.skipif(CLI is None, reason="openspec CLI is not installed")


def load_schema() -> dict:
    return yaml.safe_load(SCHEMA_FILE.read_text(encoding="utf-8"))


def artifact(schema: dict, artifact_id: str) -> dict:
    for entry in schema["artifacts"]:
        if entry["id"] == artifact_id:
            return entry
    raise AssertionError("schema declares no artifact " + repr(artifact_id))


def run_cli(args: list, cwd: Path) -> subprocess.CompletedProcess:
    assert CLI is not None
    return subprocess.run([CLI, *args], cwd=str(cwd), capture_output=True, text=True, timeout=180)


def scaffold_root(tmp_path: Path) -> Path:
    """A throwaway OpenSpec root with the project schema and config."""
    root = tmp_path / "root"
    (root / "openspec").mkdir(parents=True)
    shutil.copy(REPO_ROOT / "openspec" / "config.yaml", root / "openspec" / "config.yaml")
    shutil.copytree(SCHEMA_DIR.parent, root / "openspec" / "schemas")
    return root


def scaffold_change(tmp_path: Path, name: str = "demo") -> Path:
    root = scaffold_root(tmp_path)
    result = run_cli(["new", "change", name, "--schema", "evidence-driven"], root)
    assert result.returncode == 0, result.stderr
    return root


# --------------------------------------------------------------------------- #
# Schema structure
# --------------------------------------------------------------------------- #


def test_schema_declares_the_expected_artifact_order() -> None:
    schema = load_schema()
    assert [entry["id"] for entry in schema["artifacts"]] == ARTIFACT_ORDER
    assert schema["name"] == "evidence-driven"


def test_adversarial_review_depends_on_specs_and_design() -> None:
    assert artifact(load_schema(), "adversarial-review")["requires"] == ["specs", "design"]


def test_tasks_depend_on_the_adversarial_review() -> None:
    assert artifact(load_schema(), "tasks")["requires"] == [
        "specs",
        "design",
        "adversarial-review",
    ]


def test_apply_still_tracks_tasks() -> None:
    apply = load_schema()["apply"]
    assert apply["requires"] == ["tasks"]
    assert apply["tracks"] == "tasks.md"


def test_schema_uses_only_supported_keys() -> None:
    schema = load_schema()
    assert set(schema) <= TOP_LEVEL_KEYS
    for entry in schema["artifacts"]:
        assert set(entry) <= ARTIFACT_KEYS, entry["id"]


def test_every_artifact_template_exists() -> None:
    for entry in load_schema()["artifacts"]:
        template = entry["template"]
        assert (TEMPLATES / template).is_file(), template


def test_verification_templates_are_present() -> None:
    for name in ("code-review.md", "traceability.md", "acceptance.md"):
        assert (TEMPLATES / "verification" / name).is_file(), name


def test_adversarial_review_template_covers_its_required_sections() -> None:
    text = (TEMPLATES / "adversarial-review.md").read_text(encoding="utf-8")
    for heading in (
        "Review Scope",
        "Assumption Challenges",
        "Requirement Gaps",
        "Design Counterexamples",
        "Scientific Validity",
        "Acceptance Criteria Weaknesses",
        "Findings",
        "Review Decision",
    ):
        assert heading in text, heading
    for token in (
        "PASS_WITH_WARNINGS",
        "BLOCKED",
        "Finding ID",
        "Severity",
        "Affected artifact",
        "Evidence or reasoning",
        "Proposed resolution",
        "Status",
    ):
        assert token in text, token


def test_code_review_template_covers_its_required_fields() -> None:
    text = (TEMPLATES / "verification" / "code-review.md").read_text(encoding="utf-8")
    for token in (
        "Finding ID",
        "Severity",
        "File and location",
        "Description",
        "Reproduction or supporting evidence",
        "Recommended correction",
        "Status",
        "PASS_WITH_WARNINGS",
        "BLOCKED",
    ):
        assert token in text, token


def test_traceability_template_keeps_both_chains_and_vocabularies() -> None:
    text = (TEMPLATES / "verification" / "traceability.md").read_text(encoding="utf-8")
    for token in (
        "Engineering Traceability",
        "Scientific Traceability",
        "OBSERVED",
        "INFERRED",
        "SIMULATED",
        "UNVERIFIED",
        "PARTIALLY_VERIFIED",
        "NOT_APPLICABLE",
    ):
        assert token in text, token


# --------------------------------------------------------------------------- #
# Installed CLI compatibility
# --------------------------------------------------------------------------- #


@needs_cli
def test_cli_validates_the_evidence_driven_schema() -> None:
    result = run_cli(["schema", "validate", "evidence-driven"], REPO_ROOT)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "is valid" in result.stdout


@needs_cli
def test_cli_recognizes_the_adversarial_review_artifact(tmp_path: Path) -> None:
    root = scaffold_change(tmp_path)
    result = run_cli(["status", "--change", "demo", "--json"], root)
    assert result.returncode == 0, result.stderr
    status = json.loads(result.stdout)
    assert list(status["artifactPaths"]) == ARTIFACT_ORDER
    assert status["applyRequires"] == ["tasks"]
    assert status["schemaName"] == "evidence-driven"


@needs_cli
def test_cli_tasks_instructions_list_the_adversarial_review_dependency(
    tmp_path: Path,
) -> None:
    root = scaffold_change(tmp_path)
    result = run_cli(["instructions", "tasks", "--change", "demo"], root)
    assert result.returncode == 0, result.stderr
    missing = [line for line in result.stdout.splitlines() if "Missing:" in line]
    assert missing, result.stdout
    for artifact_id in ("specs", "design", "adversarial-review"):
        assert artifact_id in missing[0], missing[0]


@needs_cli
def test_cli_still_validates_requirement_and_scenario_format(tmp_path: Path) -> None:
    root = scaffold_change(tmp_path)
    spec = root / "openspec" / "changes" / "demo" / "specs" / "demo-capability" / "spec.md"
    spec.parent.mkdir(parents=True)
    spec.write_text(
        "# Spec Delta\n\n"
        "## ADDED Requirements\n\n"
        "### Requirement: Capability returns a constant\n"
        "The capability SHALL return the constant value 1 for every request.\n\n"
        "#### Scenario: Constant is returned\n"
        "- **WHEN** the capability is called\n"
        "- **THEN** it returns 1\n",
        encoding="utf-8",
    )
    result = run_cli(["validate", "demo"], root)
    assert result.returncode == 0, result.stdout + result.stderr


@needs_cli
def test_cli_resolves_every_existing_change_with_the_new_schema() -> None:
    changes = REPO_ROOT / "openspec" / "changes"
    names = [
        path.name
        for path in sorted(changes.iterdir())
        if path.is_dir() and path.name != "archive" and not path.name.startswith(".")
    ]
    assert names, "no in-flight change to check"
    for name in names:
        result = run_cli(["status", "--change", name, "--json"], REPO_ROOT)
        assert result.returncode == 0, name + ": " + result.stderr
        assert json.loads(result.stdout)["schemaName"] == "evidence-driven", name


# --------------------------------------------------------------------------- #
# Runtime independence
# --------------------------------------------------------------------------- #

RUNTIME_TOKENS = ("openrig", "orca", "seat", "pod", "gateway", "rig")
RUNTIME_TOKEN_RE = re.compile(
    "(?<![a-z0-9])(?:" + "|".join(RUNTIME_TOKENS) + ")(?![a-z0-9])", re.IGNORECASE
)
WORKFLOW_DOC = REPO_ROOT / "guidance" / "openspec-workflow.md"
GATE_SCRIPT = REPO_ROOT / "scripts" / "openspec_quality_gate.py"


def runtime_tokens(text: str) -> list:
    """Lines that name a specific agent runtime or orchestration framework."""
    found = []
    for number, line in enumerate(text.splitlines(), 1):
        match = RUNTIME_TOKEN_RE.search(line)
        if match:
            found.append(str(number) + ": " + match.group(0))
    return found


def test_schema_layer_names_no_agent_runtime() -> None:
    offenders = {}
    for path in sorted(SCHEMA_DIR.rglob("*")):
        if path.is_file() and path.suffix in {".md", ".yaml", ".yml"}:
            found = runtime_tokens(path.read_text(encoding="utf-8"))
            if found:
                offenders[str(path.relative_to(REPO_ROOT))] = found
    assert offenders == {}, "runtime-specific wording in the schema layer: " + str(offenders)


def test_workflow_document_is_runtime_agnostic() -> None:
    assert runtime_tokens(WORKFLOW_DOC.read_text(encoding="utf-8")) == []


def test_validator_needs_no_agent_runtime() -> None:
    source = GATE_SCRIPT.read_text(encoding="utf-8")
    assert runtime_tokens(source) == []
    modules = set(re.findall(r"^(?:import|from)[ ]+([A-Za-z_][A-Za-z0-9_]*)", source, re.MULTILINE))
    assert modules, "the import scan found no imports; the pattern is broken"
    assert modules <= set(sys.stdlib_module_names), sorted(modules - set(sys.stdlib_module_names))


def test_runtime_token_scan_actually_detects_runtime_names() -> None:
    """Guard the guard: a broken pattern must not make the checks above vacuous."""
    assert runtime_tokens("The OpenRig Lead seat dispatches the review.") != []
    assert runtime_tokens("a single-agent runtime with no orchestration layer") == []
    assert runtime_tokens("the copyright notice and the original design") == []
