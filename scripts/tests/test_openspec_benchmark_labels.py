"""The review-workflow benchmark must state what it is and what it is missing."""

from __future__ import annotations

import json
from pathlib import Path

BENCHMARK = (
    Path(__file__).resolve().parents[2] / "docs" / "benchmarks" / "openspec-review-workflow.json"
)


def load() -> dict:
    return json.loads(BENCHMARK.read_text(encoding="utf-8"))


def test_benchmark_declares_itself_illustrative() -> None:
    data = load()
    assert data["classification"] == "illustrative"
    assert "not a controlled study" in data["classification_note"]


def test_benchmark_does_not_claim_unsupported_precision() -> None:
    results = load()["results"]
    for label in ("baseline_pass_a", "improved_pass_b"):
        assert results[label]["precision"] is None
        assert results[label]["precision_note"]


def test_benchmark_marks_missing_artifacts_and_keeps_ground_truth() -> None:
    design = load()["design"]
    assert design["preserved_artifacts"] == {
        "prompts": False,
        "reviewer_outputs": False,
        "transcripts": False,
        "sandbox_repository": False,
    }
    assert design["ground_truth"]["s1 caller break after rename"] == 1
    assert design["ground_truth"]["s5 clean change (bait for false positives)"] == 0
    assert design["missing_evidence_note"]
