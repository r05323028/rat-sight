"""Synthetic graph fixture used only for deterministic demonstrations."""

from __future__ import annotations

import threading
import weakref
from collections import deque
from collections.abc import Sequence

import networkx as nx

SYNTHETIC_FIXTURE_ID = "ratsight-synthetic-graph-v1"


def _point_in_polygon(point: tuple[float, float], polygon: list[tuple[float, float]]) -> bool:
    """Strictly test a point in a simple polygon; boundary points are ineligible."""
    x, y = point
    inside = False
    for (x1, y1), (x2, y2) in zip(polygon, polygon[1:] + polygon[:1], strict=True):
        if y1 == y2 and y == y1 and min(x1, x2) <= x <= max(x1, x2):
            return False
        if (y1 > y) != (y2 > y):
            crossing = (x2 - x1) * (y - y1) / (y2 - y1) + x1
            if x == crossing:
                return False
            if x < crossing:
                inside = not inside
    return inside


def resolve_origin_cell(
    graph: nx.MultiDiGraph,
    cell_id: str,
    polygon: list[tuple[float, float]],
) -> dict[str, object]:
    """Resolve strictly in-cell graph nodes; multiple nodes seed uniformly, never snap."""
    if len(polygon) < 4 or polygon[0] != polygon[-1]:
        raise ValueError("origin cell polygon must be closed and contain at least four points")
    candidates = sorted(
        str(node_id)
        for node_id, data in graph.nodes(data=True)
        if _point_in_polygon(tuple(data["coordinates"]), polygon)
    )
    if not candidates:
        raise ValueError(f"origin cell {cell_id!r} has 0 eligible graph nodes")
    return {
        "origin_cell_id": cell_id,
        "origin_node_id": candidates[0],
        "origin_node_ids": candidates,
        "candidate_count": len(candidates),
        "resolver_version": ("strict-in-cell-v1" if len(candidates) == 1 else "uniform-in-cell-v1"),
        "classification": "UNVERIFIED",
    }


_COMPONENT_COUNTS: weakref.WeakKeyDictionary[nx.MultiDiGraph, int] = weakref.WeakKeyDictionary()
_COMPONENT_LOCK = threading.Lock()


def _component_count(graph: nx.MultiDiGraph) -> int:
    """Memoize the whole-graph component count per graph object.

    The count depends only on immutable topology, and the loader builds a new
    graph whenever the pinned source changes, so identity-keyed caching cannot
    serve stale topology to a later request.
    """
    with _COMPONENT_LOCK:
        cached = _COMPONENT_COUNTS.get(graph)
    if cached is not None:
        return cached
    count = nx.number_weakly_connected_components(graph)
    with _COMPONENT_LOCK:
        _COMPONENT_COUNTS[graph] = count
    return count


def reachability_summary(
    graph: nx.MultiDiGraph, origin: str | Sequence[str]
) -> dict[str, int | str | list[str]]:
    """Directed reachability from one or more origins plus whole-graph counts.

    Topology only: it reports which nodes a walk can reach, never which habitat,
    food source, or movement is biologically plausible. For a cell origin the
    union is reported because every eligible node can seed a walker.

    The union is computed with one multi-source breadth-first traversal: a cell
    origin can seed dozens of nodes, and repeating a full traversal per node
    dominated preview latency on the expanded extract.
    """
    origins = [str(origin)] if isinstance(origin, str) else [str(item) for item in origin]
    if not origins:
        raise ValueError("reachability requires at least one origin node")
    for node_id in origins:
        if node_id not in graph:
            raise ValueError(f"origin node {node_id!r} is not in graph")
    reachable = set(origins)
    frontier = deque(origins)
    while frontier:
        for successor in graph.successors(frontier.popleft()):
            if successor not in reachable:
                reachable.add(successor)
                frontier.append(successor)
    return {
        "origin_node_id": origins[0],
        "origin_node_ids": origins,
        "reachable_nodes": len(reachable),
        "total_nodes": int(graph.number_of_nodes()),
        # Counting membership matches subgraph(reachable).number_of_edges()
        # exactly, without materializing a 50k-node subgraph per request.
        "reachable_edges": int(
            sum(
                1 for source, target in graph.edges() if source in reachable and target in reachable
            )
        ),
        "total_edges": int(graph.number_of_edges()),
        "component_count": _component_count(graph),
    }


def create_synthetic_graph() -> nx.MultiDiGraph:
    """Return a small schematic graph; coordinates are not surveyed infrastructure."""
    graph = nx.MultiDiGraph(fixture_id=SYNTHETIC_FIXTURE_ID, classification="SIMULATED")
    nodes = {
        "n0": (121.530, 25.040),
        "n1": (121.540, 25.045),
        "n2": (121.550, 25.050),
        "n3": (121.560, 25.043),
        "n4": (121.550, 25.035),
        "n5": (121.540, 25.030),
    }
    for node_id, (longitude, latitude) in nodes.items():
        graph.add_node(
            node_id,
            coordinates=(longitude, latitude),
            layer="synthetic_schematic",
            classification="SIMULATED",
        )
    links = [
        ("n0", "n1", 1.0),
        ("n0", "n5", 1.5),
        ("n1", "n2", 2.0),
        ("n1", "n4", 1.0),
        ("n2", "n3", 1.25),
        ("n2", "n4", 0.8),
        ("n3", "n4", 1.75),
        ("n4", "n5", 1.0),
    ]
    for index, (source, target, weight) in enumerate(links):
        edge_id = f"synthetic-{index:02d}"
        common = {
            "edge_id": edge_id,
            "movement_weight": weight,
            "layer": "synthetic_schematic",
            "classification": "SIMULATED",
        }
        graph.add_edge(source, target, key=edge_id, **common)
        graph.add_edge(target, source, key=edge_id, **common)
    return graph
