#!/usr/bin/env python3
"""Reproducible performance measurements for the citizen-origin simulation path.

Measure first, optimize second. This script records timings, payload sizes and
memory for the pinned OSM surface network and the real simulation preview code
path. It invents no thresholds: the JSON report holds measurements, the source
snapshot identity they were taken against, and the environment they were taken
on, so a later run can be compared rather than guessed at.

Usage:
    uv run python scripts/benchmark_simulation.py
    uv run python scripts/benchmark_simulation.py --configs "24/12,100/30,500/50"
    uv run python scripts/benchmark_simulation.py --study-area synthetic --skip-snapshot
    uv run python scripts/benchmark_simulation.py --output bench.json

Exit codes: 0 measured, 2 required inputs unavailable, 1 unexpected error.
Measurements are engineering artifacts only: they say nothing about rodent
ecology, and they do not validate the movement model.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import statistics
import subprocess
import sys
import time
import tracemalloc
from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import networkx as nx
from ratsight_api.api.schemas import OriginSourceIdentity, SimulationPreviewRequest
from ratsight_api.application.simulation_preview import preview_simulation
from ratsight_api.domain.citizen_report_aggregates import DATASET_ID
from ratsight_api.infrastructure.database.connection import SessionLocal
from ratsight_geo.osm import load_osm_surface_graph
from ratsight_simulation.graph.network import (
    create_synthetic_graph,
    reachability_summary,
    resolve_origin_cell,
)
from ratsight_simulation.movement.random_walk import run_weighted_random_walk
from sqlalchemy.exc import SQLAlchemyError

sys.path.insert(0, str(Path(__file__).resolve().parent))

from citizen_origin_coverage import (  # noqa: E402
    CITIZEN_REPORT_CLASSIFICATION,
    CITIZEN_REPORT_DATA_CLASS,
    SUPPRESSION_MINIMUM,
    load_published_snapshot,
)

DEFAULT_CONFIGS = "24/12,100/30,500/50"
BENCHMARK_SCHEMA_VERSION = "1"

CAPACITY_NOTES: tuple[str, ...] = (
    "Timings include digest verification on every graph load; only parsing is cached.",
    "Payload bytes are the JSON body of one preview response, not HTTP framing.",
    "The walk is pure Python over a MultiDiGraph; larger walker/step products scale "
    "roughly linearly with walkers x steps.",
    "Memory figures come from tracemalloc allocation peaks, not resident set size.",
)


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def _timed(operation: Callable[[], Any]) -> tuple[float, Any]:
    started = time.perf_counter()
    value = operation()
    return (time.perf_counter() - started) * 1000.0, value


def _percentile(values: Sequence[float], fraction: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round(fraction * (len(ordered) - 1))))
    return round(ordered[index], 3)


def parse_configs(spec: str) -> list[tuple[int, int]]:
    """Parse '24/12,100/30' into walker/step pairs, rejecting nonsense."""
    configs: list[tuple[int, int]] = []
    for chunk in spec.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        try:
            walkers, steps = (int(part) for part in chunk.split("/", maxsplit=1))
        except ValueError as exc:
            raise ValueError(
                f"invalid benchmark config {chunk!r}; expected '<walkers>/<steps>'"
            ) from exc
        if walkers < 1 or steps < 1:
            raise ValueError(f"benchmark config {chunk!r} must use positive walkers and steps")
        configs.append((walkers, steps))
    if not configs:
        raise ValueError("at least one benchmark config is required")
    return configs


def environment() -> dict[str, Any]:
    total_bytes: int | None = None
    try:
        total_bytes = os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")
    except (AttributeError, ValueError, OSError):
        total_bytes = None
    return {
        "measured_at": _now(),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor() or "unknown",
        "cpu_count": os.cpu_count(),
        "total_memory_bytes": total_bytes,
        "networkx": nx.__version__,
    }


def measure_untraced_cold_load(source: str | None) -> float | None:
    """Cold load in a fresh interpreter so tracing overhead is excluded."""
    code = (
        "import json, time\n"
        "from ratsight_geo.osm import load_osm_surface_graph\n"
        f"source = json.loads({json.dumps(json.dumps(source))})\n"
        "started = time.perf_counter()\n"
        "load_osm_surface_graph(source)\n"
        "print((time.perf_counter() - started) * 1000.0)\n"
    )
    completed = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=False
    )
    if completed.returncode != 0:
        return None
    try:
        return round(float(completed.stdout.strip().splitlines()[-1]), 3)
    except (IndexError, ValueError):
        return None


def measure_graph_load(
    source: str | None, *, study_area: str
) -> tuple[dict[str, Any], nx.MultiDiGraph]:
    """Cold load is the first call in this process; warm loads hit the parse cache."""
    tracemalloc.start()
    cold_ms, graph = _timed(lambda: _load(study_area, source))
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    warm_samples: list[float] = []
    for _ in range(3):
        warm_ms, _ = _timed(lambda: _load(study_area, source))
        warm_samples.append(warm_ms)

    untraced_ms = measure_untraced_cold_load(source) if study_area != "synthetic" else None
    metadata = dict(graph.graph)
    return {
        "study_area": study_area,
        "source": source or metadata.get("source_id"),
        "cold_load_ms": round(cold_ms, 3),
        "cold_load_ms_untraced": untraced_ms,
        "cold_load_note": "cold_load_ms is traced (upper bound); cold_load_ms_untraced "
        "is a fresh interpreter without tracemalloc",
        "warm_load_ms_samples": [round(sample, 3) for sample in warm_samples],
        "warm_load_ms_median": round(statistics.median(warm_samples), 3),
        "graph_memory_peak_bytes": peak,
        "graph_memory_current_bytes": current,
        "node_count": int(graph.number_of_nodes()),
        "edge_count": int(graph.number_of_edges()),
        "network_provenance": {
            key: metadata.get(key)
            for key in (
                "source_id",
                "source_sha256",
                "resource_version",
                "license",
                "attribution",
                "source_crs",
                "coverage",
            )
        },
    }, graph


def _load(study_area: str, source: str | None) -> nx.MultiDiGraph:
    if study_area == "synthetic":
        return create_synthetic_graph()
    return load_osm_surface_graph(source)


def measure_origin_resolution(
    graph: nx.MultiDiGraph, cells: Sequence[Any], *, cell_limit: int
) -> dict[str, Any]:
    """Time strict in-cell resolution across a bounded sample of eligible cells."""
    eligible = [
        cell
        for cell in cells
        if cell.suppression_satisfied
        and cell.classification == CITIZEN_REPORT_CLASSIFICATION
        and cell.report_type == "sighting"
    ]
    sample = eligible[:cell_limit] if cell_limit > 0 else eligible
    samples: list[float] = []
    candidate_counts: list[int] = []
    zero_candidate = 0
    for cell in sample:
        elapsed_ms, resolved = _timed(
            lambda cell=cell: resolve_origin_cell(graph, cell.feature_id, cell.polygon)
        )
        if resolved is None:
            zero_candidate += 1
            continue
        samples.append(elapsed_ms)
        candidate_counts.append(int(resolved["candidate_count"]))

    return {
        "eligible_cells_total": len(eligible),
        "cells_measured": len(sample),
        "resolved": len(samples),
        "zero_candidate": zero_candidate,
        "per_cell_ms_median": _percentile(samples, 0.5),
        "per_cell_ms_p90": _percentile(samples, 0.9),
        "per_cell_ms_max": round(max(samples), 3) if samples else 0.0,
        "candidates_min": min(candidate_counts, default=0),
        "candidates_median": int(statistics.median(candidate_counts)) if candidate_counts else 0,
        "candidates_max": max(candidate_counts, default=0),
        "sample_cell": sample[0].feature_id if sample else None,
    }


def measure_reachability(graph: nx.MultiDiGraph, origin_node_ids: Sequence[str]) -> dict[str, Any]:
    elapsed_ms, summary = _timed(lambda: reachability_summary(graph, list(origin_node_ids)))
    return {"elapsed_ms": round(elapsed_ms, 3), **summary}


def measure_walk(
    graph: nx.MultiDiGraph,
    origin_node_ids: Sequence[str],
    configs: Sequence[tuple[int, int]],
    *,
    seed: int,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for walkers, steps in configs:
        elapsed_ms, stats = _timed(
            lambda walkers=walkers, steps=steps: run_weighted_random_walk(
                graph,
                walkers=walkers,
                steps=steps,
                seed=seed,
                start_nodes=list(origin_node_ids),
            )
        )
        results.append(
            {
                "walkers": walkers,
                "steps": steps,
                "seed": seed,
                "elapsed_ms": round(elapsed_ms, 3),
                "ms_per_walker": round(elapsed_ms / walkers, 3),
                "distinct_nodes_visited": len(getattr(stats, "counts", {}) or {}),
            }
        )
    return results


def measure_preview(
    session: Any,
    *,
    feature_id: str,
    source: OriginSourceIdentity,
    configs: Sequence[tuple[int, int]],
    seed: int,
) -> list[dict[str, Any]]:
    """Time the real preview path plus JSON serialization and payload size."""
    results: list[dict[str, Any]] = []
    for walkers, steps in configs:
        request = SimulationPreviewRequest(
            study_area="taipei_osm_songshan",
            origin_cell_id=feature_id,
            origin_source=source,
            walkers=walkers,
            duration_steps=steps,
            random_seed=seed,
        )
        try:
            elapsed_ms, response = _timed(
                lambda request=request: preview_simulation(request, session=session)
            )
        except Exception as exc:  # noqa: BLE001 - record the failure, do not hide it
            results.append(
                {
                    "walkers": walkers,
                    "steps": steps,
                    "status": "failed",
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )
            continue
        serialize_ms, payload = _timed(
            lambda response=response: json.dumps(response, ensure_ascii=False)
        )
        results.append(
            {
                "walkers": walkers,
                "steps": steps,
                "status": "ok",
                "preview_ms": round(elapsed_ms, 3),
                "serialize_ms": round(serialize_ms, 3),
                "payload_bytes": len(payload.encode("utf-8")),
                "payload_nodes": len(response.get("network_subset", {}).get("nodes", []))
                if isinstance(response.get("network_subset"), dict)
                else None,
            }
        )
    return results


def build_report(
    *,
    study_area: str,
    source: str | None,
    configs: Sequence[tuple[int, int]],
    cell_limit: int,
    seed: int,
    skip_snapshot: bool,
) -> tuple[dict[str, Any], int]:
    graph_report, graph = measure_graph_load(source, study_area=study_area)
    report: dict[str, Any] = {
        "benchmark_schema_version": BENCHMARK_SCHEMA_VERSION,
        "classification": "ENGINEERING_MEASUREMENT",
        "environment": environment(),
        "graph": graph_report,
        "seed": seed,
        "configs": [{"walkers": walkers, "steps": steps} for walkers, steps in configs],
        "capacity_notes": list(CAPACITY_NOTES),
    }
    if skip_snapshot or study_area == "synthetic":
        report["snapshot"] = {"available": False, "reason": "snapshot measurements skipped"}
        report["origin_resolution"] = None
        report["reachability"] = None
        report["walks"] = []
        report["previews"] = []
        return report, 0

    try:
        resource_version, cells, digest, provenance = load_published_snapshot_records()
    except LookupError as exc:
        report["snapshot"] = {"available": False, "reason": str(exc)}
        report["origin_resolution"] = None
        report["reachability"] = None
        report["walks"] = []
        report["previews"] = []
        return report, 2
    except SQLAlchemyError as exc:
        report["snapshot"] = {"available": False, "reason": f"database unavailable: {exc}"}
        report["origin_resolution"] = None
        report["reachability"] = None
        report["walks"] = []
        report["previews"] = []
        return report, 2

    report["snapshot"] = {
        "available": True,
        "resource_version": resource_version,
        "content_sha256": digest,
        "classification": CITIZEN_REPORT_CLASSIFICATION,
        "data_class": CITIZEN_REPORT_DATA_CLASS,
        "suppression_minimum": SUPPRESSION_MINIMUM,
        "published_cells": len(cells),
        "provenance": provenance,
    }
    report["origin_resolution"] = measure_origin_resolution(graph, cells, cell_limit=cell_limit)

    eligible = [
        cell
        for cell in cells
        if cell.suppression_satisfied
        and cell.classification == CITIZEN_REPORT_CLASSIFICATION
        and cell.report_type == "sighting"
    ]
    if not eligible:
        report["reachability"] = None
        report["walks"] = []
        report["previews"] = []
        report["snapshot"]["eligible_origin_cells"] = 0
        return report, 0

    sample = eligible[0]
    resolved = resolve_origin_cell(graph, sample.feature_id, sample.polygon)
    origin_node_ids = [str(node) for node in cast(Sequence[str], resolved["origin_node_ids"])]
    report["origin_resolution"]["sample_cell"] = sample.feature_id
    report["origin_resolution"]["sample_candidate_count"] = len(origin_node_ids)
    report["reachability"] = measure_reachability(graph, origin_node_ids)
    report["walks"] = measure_walk(graph, origin_node_ids, configs, seed=seed)

    origin_source = OriginSourceIdentity(
        dataset_id=DATASET_ID,
        resource_version=resource_version,
        content_sha256=digest or "0" * 64,
    )
    with SessionLocal() as session:
        report["previews"] = measure_preview(
            session,
            feature_id=sample.feature_id,
            source=origin_source,
            configs=configs,
            seed=seed,
        )
    return report, 0


def load_published_snapshot_records() -> tuple[str, list[Any], str | None, dict[str, Any] | None]:
    return load_published_snapshot(DATASET_ID)


def render_summary(report: dict[str, Any]) -> str:
    graph = report["graph"]
    lines = [
        f"environment    {report['environment']['platform']} · "
        f"python {report['environment']['python']}",
        f"graph          {graph['node_count']} nodes · {graph['edge_count']} edges",
        f"cold load      {graph.get('cold_load_ms_untraced') or graph['cold_load_ms']} ms "
        f"(traced {graph['cold_load_ms']} ms)",
        f"warm load      {graph['warm_load_ms_median']} ms (median of "
        f"{len(graph['warm_load_ms_samples'])})",
        f"graph memory   {graph['graph_memory_peak_bytes'] / 1_048_576:.1f} MiB peak",
    ]
    resolution = report.get("origin_resolution")
    if resolution:
        lines.append(
            f"resolve cell   median {resolution['per_cell_ms_median']} ms · "
            f"p90 {resolution['per_cell_ms_p90']} ms · max {resolution['per_cell_ms_max']} ms "
            f"over {resolution['cells_measured']} cells"
        )
    reachability = report.get("reachability")
    if reachability:
        lines.append(
            f"reachability   {reachability['elapsed_ms']} ms "
            f"({reachability['reachable_nodes']}/{reachability['total_nodes']} nodes, "
            f"{reachability['component_count']} components)"
        )
    for walk in report.get("walks") or []:
        lines.append(
            f"walk {walk['walkers']}/{walk['steps']:<3} {walk['elapsed_ms']} ms "
            f"({walk['ms_per_walker']} ms/walker)"
        )
    for preview in report.get("previews") or []:
        if preview.get("status") != "ok":
            label = f"preview {preview['walkers']}/{preview['steps']}"
            lines.append(f"{label} FAILED {preview['error']}")
            continue
        lines.append(
            f"preview {preview['walkers']}/{preview['steps']:<3} {preview['preview_ms']} ms · "
            f"serialize {preview['serialize_ms']} ms · {preview['payload_bytes']} bytes"
        )
    if report.get("snapshot", {}).get("available"):
        snapshot = report["snapshot"]
        lines.append(
            f"snapshot       {snapshot['resource_version']} · "
            f"{snapshot['published_cells']} cells · sha256 {snapshot['content_sha256']}"
        )
    else:
        lines.append(f"snapshot       unavailable: {report.get('snapshot', {}).get('reason')}")
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--study-area", default="taipei_osm_songshan")
    parser.add_argument("--osm-source", default=None)
    parser.add_argument("--configs", default=DEFAULT_CONFIGS)
    parser.add_argument("--cell-limit", type=int, default=25)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--skip-snapshot", action="store_true")
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args(argv)

    try:
        configs = parse_configs(args.configs)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    try:
        report, status = build_report(
            study_area=args.study_area,
            source=args.osm_source,
            configs=configs,
            cell_limit=args.cell_limit,
            seed=args.seed,
            skip_snapshot=args.skip_snapshot,
        )
    except (FileNotFoundError, ValueError) as exc:
        print(f"network unavailable: {exc}", file=sys.stderr)
        return 2

    print(render_summary(report))
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(f"report written to {args.output}")
    return status


if __name__ == "__main__":
    raise SystemExit(main())
