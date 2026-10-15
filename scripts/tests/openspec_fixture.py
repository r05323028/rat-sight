from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "scripts/tests/fixtures/quality_gate"


def prepare_repo(destination: Path) -> Path:
    repo = destination / "repo"
    shutil.copytree(FIXTURE, repo)
    shutil.copy2(ROOT / "openspec/config.yaml", repo / "openspec/config.yaml")
    shutil.copytree(
        ROOT / "openspec/schemas/evidence-driven",
        repo / "openspec/schemas/evidence-driven",
    )
    return repo
