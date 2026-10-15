#!/usr/bin/env python3
"""Regression checks for RatSight's role-scoped OpenRig startup guidance."""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RIG_PATH = ROOT / "rig.yaml"
AGENTS_PATH = ROOT / "AGENTS.md"
ROLES = {
    "lead": "guidance/lead.md",
    "frontend": "guidance/frontend.md",
    "backend": "guidance/backend.md",
    "infrastructure": "guidance/infrastructure.md",
    "public-health": "guidance/public-health.md",
    "modeler": "guidance/math-modeler.md",
    "researcher": "guidance/research-scientist.md",
    "reviewer": "guidance/reviewer.md",
    "qa": "guidance/qa.md",
}
SHARED = ("guidance/CULTURE.md", "guidance/project.md")
ON_DEMAND = (
    "guidance/openspec-workflow.md",
    "guidance/human-escalation.md",
)
errors: list[str] = []

rig = RIG_PATH.read_text(encoding="utf-8")
agents = AGENTS_PATH.read_text(encoding="utf-8")

role_ids = "|".join(map(re.escape, ROLES))
role_block = r"<!-- BEGIN OpenRig MANAGED BLOCK: guidance/(?:" + role_ids + r")\.md -->"
if re.search(role_block, agents):
    errors.append("AGENTS.md contains role-specific OpenRig managed guidance")

pods = rig.split("\npods:", 1)[1].split("\nedges:", 1)[0]
member_pattern = re.compile(r"(?ms)^      - id: ([^\n]+)\n(.*?)(?=^      - id: |^  - id: |\Z)")
members = {match.group(1).strip(): match.group(0) for match in member_pattern.finditer(pods)}
if set(members) != set(ROLES):
    errors.append(f"expected nine configured roles, found {sorted(members)}")

for role, path in ROLES.items():
    block = members.get(role, "")
    member_paths = re.findall(r"^\s+- path: (.+)$", block, re.MULTILINE)
    if member_paths != [path]:
        errors.append(f"{role}: expected only its own role startup, found {member_paths}")
    for other_role, other_path in ROLES.items():
        if other_role != role and f"path: {other_path}" in block:
            errors.append(f"{role}: also receives {other_role} guidance")
    for required in (
        "orientation: role",
        "delivery_hint: send_text",
        "required: true",
        "applies_on: [fresh_start]",
    ):
        if required not in block:
            errors.append(f"{role}: missing {required}")
    if not (ROOT / path).is_file():
        errors.append(f"missing role guidance file: {path}")
    if f"path: {path}" in rig.split("\npods:", 1)[0]:
        errors.append(f"{role}: role guidance appears in rig-wide startup")

rig_wide = rig.split("\npods:", 1)[0]
for path in SHARED:
    if rig_wide.count(f"path: {path}") != 1:
        errors.append(f"expected one rig-wide startup reference to {path}")
    if not (ROOT / path).is_file():
        errors.append(f"missing shared guidance file: {path}")
for path in ON_DEMAND:
    if not (ROOT / path).is_file():
        errors.append(f"missing on-demand workflow: {path}")
    if f"`{path}`" not in (ROOT / ROLES["lead"]).read_text(encoding="utf-8"):
        errors.append(f"lead guidance does not reference {path}")
if rig_wide.count("delivery_hint: send_text") != len(SHARED):
    errors.append("shared startup files must each use send_text")
if rig_wide.count("applies_on: [fresh_start]") != len(SHARED):
    errors.append("shared startup files must be fresh-start only")
if "guidance_merge" in rig:
    errors.append("RigSpec still uses guidance_merge; scoped guidance must not enter AGENTS.md")

startup_paths = re.findall(r"^\s+- path: (.+)$", rig, re.MULTILINE)
expected_startups = len(ROLES) + len(SHARED)
if len(startup_paths) != expected_startups:
    errors.append(f"expected {expected_startups} startup files, found {len(startup_paths)}")
if len(startup_paths) != len(set(startup_paths)):
    errors.append("duplicate startup file paths found")
for path in startup_paths:
    if not (ROOT / path).is_file():
        errors.append(f"missing startup file: {path}")
if rig_wide.count("required: true") != len(SHARED):
    errors.append("shared startup files must each be required")

if errors:
    print("Guidance config check failed:", file=sys.stderr)
    for error in errors:
        print(f"- {error}", file=sys.stderr)
    raise SystemExit(1)

print("Guidance config OK: 9 isolated role files, 2 shared files, no role managed blocks.")
