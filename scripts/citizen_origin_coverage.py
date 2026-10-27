#!/usr/bin/env python3
"""Repeatable coverage diagnostics for published citizen-report origin cells.

This tool answers one engineering question: given the *current* published
citizen-report aggregate snapshot and the *pinned* OSM surface network, how many
eligible origin cells resolve to strictly in-cell graph nodes, and which do not?

It never fabricates coverage. A cell that resolves proves geometric containment
in the network graph only. A 250 m aggregate cell is not an animal location, a
missing cell is not a zero count, and road geometry is not validated rodent
movement ecology. Cell counts are UNVERIFIED citizen reports and are never
simulation inputs or weights.

Usage:
    uv run python scripts/citizen_origin_coverage.py
    uv run python scripts/citizen_origin_coverage.py --output coverage.json
    uv run python scripts/citizen_origin_coverage.py --compare earlier.json

Exit codes: 0 measured, 2 snapshot or network unavailable, 1 unexpected error.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import Counter
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import networkx as nx
from ratsight_api.domain.citizen_report_aggregates import (
    CELL_SIZE_METERS,
    CITIZEN_REPORT_CLASSIFICATION,
    CITIZEN_REPORT_DATA_CLASS,
    DATASET_ID,
    SUPPRESSION_MINIMUM,
    origin_eligibility,
)
from ratsight_api.infrastructure.database.connection import SessionLocal
from ratsight_api.infrastructure.database.models import CitizenReportCell
from ratsight_geo.osm import load_osm_surface_graph
from ratsight_simulation.graph.network import resolve_origin_cell
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError

CANDIDATE_BUCKETS: tuple[tuple[str, int, int | None], ...] = (
    ("1", 1, 1),
    ("2-4", 2, 4),
    ("5-9", 5, 9),
    ("10-49", 10, 49),
    ("50-99", 50, 99),
    ("100+", 100, None),
)

COVERAGE_LIMITATIONS: tuple[str, ...] = (
    "Resolution proves only that a graph node lies inside the published polygon; "
    "it is not evidence that rodents occupy the cell.",
    "A 250 m aggregate cell is not an animal location, and its report count is "
    "not an animal count.",
    "Unresolvable cells stay ineligible. This tool never snaps a cell to a "
    "distant road or substitutes another cell.",
    "The network is a bounded OSM road extract, not validated rodent movement "
    "ecology; its coverage is limited to the pinned export extent.",
    "Absence of a published cell is suppressed or missing data, never a zero report count.",
)


@dataclass(frozen=True)
class PublishedCell:
    """One published aggregate row, reduced to what coverage needs."""

    cell_id: str
    month: str
    report_type: str
    report_count: int | None
    data_class: str
    classification: str
    polygon: list[tuple[float, float]]

    @property
    def feature_id(self) -> str:
        return f"{self.cell_id}:{self.month}:{self.report_type}"

    @property
    def suppression_satisfied(self) -> bool:
        if self.data_class != CITIZEN_REPORT_DATA_CLASS:
            return self.report_count is None
        return self.report_count is not None and self.report_count >= SUPPRESSION_MINIMUM


def _histogram(candidate_counts: Sequence[int]) -> dict[str, int]:
    histogram: dict[str, int] = {label: 0 for label, _, _ in CANDIDATE_BUCKETS}
    for count in candidate_counts:
        for label, low, high in CANDIDATE_BUCKETS:
            if count >= low and (high is None or count <= high):
                histogram[label] += 1
                break
    return histogram


def _percentile(values: Sequence[int], fraction: float) -> int:
    if not values:
        return 0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round(fraction * (len(ordered) - 1))))
    return ordered[index]


def summarize_coverage(
    cells: Sequence[PublishedCell],
    graph: nx.MultiDiGraph,
    *,
    dataset_id: str,
    resource_version: str,
    content_sha256: str | None,
    provenance: dict[str, Any] | None,
    resolver: Callable[
        [nx.MultiDiGraph, str, list[tuple[float, float]]], dict[str, Any]
    ] = resolve_origin_cell,
) -> dict[str, Any]:
    """Summarize origin coverage for one snapshot; pure except for the resolver."""
    ineligible: Counter[str] = Counter()
    ineligible_reasons: dict[str, str] = {}
    zero_candidate: list[dict[str, Any]] = []
    candidate_counts: list[int] = []
    resolver_versions: Counter[str] = Counter()
    eligible_cells = 0

    for cell in cells:
        eligible, reason = origin_eligibility(cell.report_type)
        if not eligible:
            ineligible[cell.report_type] += 1
            ineligible_reasons[cell.report_type] = reason
            continue
        if not cell.suppression_satisfied or cell.classification != CITIZEN_REPORT_CLASSIFICATION:
            ineligible[cell.report_type] += 1
            ineligible_reasons[cell.report_type] = "stored cell is not publishable"
            continue
        eligible_cells += 1
        try:
            resolved = resolver(graph, cell.feature_id, cell.polygon)
        except ValueError as exc:
            zero_candidate.append({"feature_id": cell.feature_id, "reason": str(exc)})
            continue
        candidate_counts.append(int(resolved["candidate_count"]))
        resolver_versions[str(resolved["resolver_version"])] += 1

    network = graph.graph
    return {
        "coverage_schema_version": "1",
        "classification": "ENGINEERING_DIAGNOSTIC",
        "source": {
            "dataset_id": dataset_id,
            "resource_version": resource_version,
            "content_sha256": content_sha256,
            "classification": CITIZEN_REPORT_CLASSIFICATION,
            "cell_size_meters": CELL_SIZE_METERS,
            "suppression_minimum": SUPPRESSION_MINIMUM,
            "provenance": provenance,
        },
        "network": {
            "source_id": network.get("source_id"),
            "source_sha256": network.get("source_sha256"),
            "resource_version": network.get("resource_version"),
            "license": network.get("license"),
            "attribution": network.get("attribution"),
            "source_crs": network.get("source_crs"),
            "coverage": network.get("coverage"),
            "node_count": graph.number_of_nodes(),
            "edge_count": graph.number_of_edges(),
        },
        "cell_counts": {
            "published": len(cells),
            "eligible_origin_cells": eligible_cells,
            "resolved": len(candidate_counts),
            "zero_candidate": len(zero_candidate),
            "context_only": sum(ineligible.values()),
        },
        "context_only_by_report_type": dict(sorted(ineligible.items())),
        "context_only_reasons": dict(sorted(ineligible_reasons.items())),
        "candidate_counts": {
            "total": sum(candidate_counts),
            "min": min(candidate_counts, default=0),
            "median": int(statistics.median(candidate_counts)) if candidate_counts else 0,
            "p90": _percentile(candidate_counts, 0.9),
            "max": max(candidate_counts, default=0),
            "histogram": _histogram(candidate_counts),
        },
        "resolver_versions": dict(sorted(resolver_versions.items())),
        "unresolvable_cells": zero_candidate,
        "limitations": list(COVERAGE_LIMITATIONS),
    }


def _parse_polygon(raw: str) -> list[tuple[float, float]]:
    geometry = json.loads(raw)
    if geometry.get("type") != "Polygon":
        raise ValueError(f"unsupported aggregate geometry type: {geometry.get('type')!r}")
    return [(float(x), float(y)) for x, y in geometry["coordinates"][0]]


def load_published_snapshot(
    dataset_id: str,
) -> tuple[str, list[PublishedCell], str | None, dict[str, Any] | None]:
    """Read the latest published snapshot; raises LookupError when absent."""
    with SessionLocal() as session:
        latest = session.execute(
            select(func.max(CitizenReportCell.resource_version)).where(
                CitizenReportCell.dataset_id == dataset_id
            )
        ).scalar_one_or_none()
        if latest is None:
            raise LookupError(f"no published citizen-report cells for dataset {dataset_id!r}")
        rows = session.execute(
            select(
                CitizenReportCell.cell_id,
                CitizenReportCell.month,
                CitizenReportCell.report_type,
                CitizenReportCell.report_count,
                CitizenReportCell.data_class,
                CitizenReportCell.classification,
                CitizenReportCell.content_sha256,
                CitizenReportCell.provenance,
                func.ST_AsGeoJSON(CitizenReportCell.geometry).label("geometry"),
            ).where(
                CitizenReportCell.dataset_id == dataset_id,
                CitizenReportCell.resource_version == latest,
            )
        ).all()

    cells: list[PublishedCell] = []
    digests: set[str] = set()
    provenance: dict[str, Any] | None = None
    for row in rows:
        digests.add(str(row.content_sha256))
        if provenance is None and isinstance(row.provenance, dict):
            provenance = dict(row.provenance)
        cells.append(
            PublishedCell(
                cell_id=str(row.cell_id),
                month=str(row.month),
                report_type=str(row.report_type),
                report_count=None if row.report_count is None else int(row.report_count),
                data_class=str(row.data_class),
                classification=str(row.classification),
                polygon=_parse_polygon(str(row.geometry)),
            )
        )
    digest = digests.pop() if len(digests) == 1 else None
    return str(latest), cells, digest, provenance


def compare_snapshots(current: dict[str, Any], previous: dict[str, Any]) -> dict[str, Any]:
    """Report source-version and coverage drift without failing on new cells."""
    current_source = current["source"]
    previous_source = previous["source"]
    current_cells = current["cell_counts"]
    previous_cells = previous["cell_counts"]
    return {
        "previous_resource_version": previous_source["resource_version"],
        "current_resource_version": current_source["resource_version"],
        "resource_version_changed": (
            previous_source["resource_version"] != current_source["resource_version"]
        ),
        "content_sha256_changed": (
            previous_source["content_sha256"] != current_source["content_sha256"]
        ),
        "published_delta": current_cells["published"] - previous_cells["published"],
        "resolved_delta": current_cells["resolved"] - previous_cells["resolved"],
        "zero_candidate_delta": current_cells["zero_candidate"] - previous_cells["zero_candidate"],
        "network_source_id_changed": (
            current["network"]["source_id"] != previous["network"]["source_id"]
        ),
        "network_source_sha256_changed": (
            current["network"]["source_sha256"] != previous["network"]["source_sha256"]
        ),
    }


def render_summary(report: dict[str, Any]) -> str:
    source = report["source"]
    network = report["network"]
    counts = report["cell_counts"]
    candidates = report["candidate_counts"]
    lines = [
        f"dataset        {source['dataset_id']} @ {source['resource_version']}",
        f"content sha256 {source['content_sha256']}",
        f"network        {network['source_id']} ({network['node_count']} nodes, "
        f"{network['edge_count']} edges)",
        f"published      {counts['published']} cells",
        f"eligible       {counts['eligible_origin_cells']} origin cells",
        f"resolved       {counts['resolved']}",
        f"zero-candidate {counts['zero_candidate']}",
        f"context-only   {counts['context_only']} {report['context_only_by_report_type']}",
        f"candidates     min {candidates['min']} · median {candidates['median']} · "
        f"p90 {candidates['p90']} · max {candidates['max']}",
        f"distribution   {candidates['histogram']}",
    ]
    if report.get("comparison"):
        lines.append(f"comparison     {report['comparison']}")
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-id", default=DATASET_ID)
    parser.add_argument(
        "--osm-source",
        default=None,
        help="Override the pinned OSM extract path (digest is still verified).",
    )
    parser.add_argument("--output", type=Path, default=None, help="Write the JSON report here.")
    parser.add_argument(
        "--compare",
        type=Path,
        default=None,
        help="Compare against a previous JSON report to detect source-version changes.",
    )
    args = parser.parse_args(argv)

    try:
        resource_version, cells, digest, provenance = load_published_snapshot(args.dataset_id)
    except LookupError as exc:
        print(f"snapshot unavailable: {exc}", file=sys.stderr)
        return 2
    except SQLAlchemyError as exc:
        print(f"database unavailable: {exc}", file=sys.stderr)
        return 2
    try:
        graph = load_osm_surface_graph(args.osm_source)
    except (FileNotFoundError, ValueError) as exc:
        print(f"network unavailable: {exc}", file=sys.stderr)
        return 2

    report = summarize_coverage(
        cells,
        graph,
        dataset_id=args.dataset_id,
        resource_version=resource_version,
        content_sha256=digest,
        provenance=provenance,
    )
    if args.compare is not None:
        previous = json.loads(args.compare.read_text(encoding="utf-8"))
        report["comparison"] = compare_snapshots(report, previous)

    print(render_summary(report))
    if args.output is not None:
        args.output.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(f"report written to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
