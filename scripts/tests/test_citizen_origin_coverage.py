"""Tests for the citizen-report origin coverage diagnostics."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

import networkx as nx
import pytest

MODULE_PATH = Path(__file__).resolve().parents[1] / "citizen_origin_coverage.py"
_SPEC = importlib.util.spec_from_file_location("citizen_origin_coverage", MODULE_PATH)
assert _SPEC is not None and _SPEC.loader is not None
coverage = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = coverage
_SPEC.loader.exec_module(coverage)

INSIDE_POLYGON = [(0.4, 0.4), (0.7, 0.4), (0.7, 0.6), (0.4, 0.6), (0.4, 0.4)]
EMPTY_POLYGON = [(8.0, 8.0), (8.2, 8.0), (8.2, 8.2), (8.0, 8.2), (8.0, 8.0)]


def _graph() -> nx.MultiDiGraph:
    graph = nx.MultiDiGraph(
        source_id="test-extract.osm",
        source_sha256="a" * 64,
        resource_version="2026-10-27T00:00:00Z",
        license="ODbL 1.0",
        attribution="© OpenStreetMap contributors",
        source_crs="EPSG:4326",
        coverage="test bbox",
    )
    for node_id, coordinates in {"a": (0.5, 0.5), "b": (0.6, 0.5), "c": (5.0, 5.0)}.items():
        graph.add_node(node_id, coordinates=coordinates)
    return graph


def _cell(**overrides: Any) -> Any:
    values: dict[str, Any] = {
        "cell_id": "g250m:1:2",
        "month": "2026-05",
        "report_type": "sighting",
        "report_count": 4,
        "data_class": "CITIZEN_REPORT_AGGREGATE",
        "classification": "UNVERIFIED",
        "polygon": INSIDE_POLYGON,
    }
    values.update(overrides)
    return coverage.PublishedCell(**values)


def _summarize(cells: list[Any]) -> dict[str, Any]:
    return coverage.summarize_coverage(
        cells,
        _graph(),
        dataset_id="ratdar-taipei-public-export",
        resource_version="2026-05-01T00:00:00Z",
        content_sha256="b" * 64,
        provenance={"attribution": "fixture"},
    )


def test_summarize_counts_resolved_zero_candidate_and_context_only() -> None:
    report = _summarize(
        [
            _cell(),
            _cell(cell_id="g250m:1:3", polygon=EMPTY_POLYGON),
            _cell(cell_id="g250m:1:4", report_type="bait_station"),
            _cell(cell_id="g250m:1:5", report_type="other"),
        ]
    )

    assert report["cell_counts"] == {
        "published": 4,
        "eligible_origin_cells": 2,
        "resolved": 1,
        "zero_candidate": 1,
        "context_only": 2,
    }
    assert report["context_only_by_report_type"] == {"bait_station": 1, "other": 1}
    assert report["context_only_reasons"] == {
        "bait_station": "context_only_bait_station",
        "other": "context_only_other",
    }
    assert report["unresolvable_cells"][0]["feature_id"] == "g250m:1:3:2026-05:sighting"
    assert "0 eligible graph nodes" in report["unresolvable_cells"][0]["reason"]
    assert report["candidate_counts"]["min"] == 2
    assert report["resolver_versions"] == {"uniform-in-cell-v1": 1}
    assert report["network"]["node_count"] == 3
    assert report["source"]["content_sha256"] == "b" * 64
    assert report["classification"] == "ENGINEERING_DIAGNOSTIC"


def test_suppressed_sighting_cell_never_becomes_an_origin() -> None:
    report = _summarize([_cell(report_count=2)])

    assert report["cell_counts"]["eligible_origin_cells"] == 0
    assert report["cell_counts"]["resolved"] == 0
    assert report["context_only_by_report_type"] == {"sighting": 1}


def test_candidate_histogram_buckets_every_resolved_cell() -> None:
    cells = [_cell(cell_id=f"g250m:2:{index}") for index in range(4)]
    report = _summarize(cells)

    histogram = report["candidate_counts"]["histogram"]
    assert list(histogram) == ["1", "2-4", "5-9", "10-49", "50-99", "100+"]
    assert histogram["2-4"] == 4
    assert sum(histogram.values()) == report["cell_counts"]["resolved"] == 4
    assert report["candidate_counts"]["total"] == 8


def test_compare_reports_source_drift_without_failing_on_new_cells() -> None:
    previous = _summarize([_cell()])
    current = _summarize([_cell(), _cell(cell_id="g250m:9:9")])
    current["source"]["resource_version"] = "2026-06-01T00:00:00Z"
    current["source"]["content_sha256"] = "c" * 64

    comparison = coverage.compare_snapshots(current, previous)

    assert comparison["resource_version_changed"] is True
    assert comparison["content_sha256_changed"] is True
    assert comparison["published_delta"] == 1
    assert comparison["resolved_delta"] == 1
    assert comparison["zero_candidate_delta"] == 0
    assert comparison["network_source_sha256_changed"] is False


def test_missing_snapshot_is_reported_as_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    def absent(_dataset_id: str) -> Any:
        raise LookupError("no published citizen-report cells for dataset 'x'")

    monkeypatch.setattr(coverage, "load_published_snapshot", absent)

    assert coverage.main(["--dataset-id", "x"]) == 2
