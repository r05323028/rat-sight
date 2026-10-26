"""Synthetic graph fixture used only for deterministic demonstrations."""

from __future__ import annotations

import networkx as nx

SYNTHETIC_FIXTURE_ID = "ratsight-synthetic-graph-v1"


def reachability_summary(graph: nx.MultiDiGraph, origin: str) -> dict[str, int | str]:
    """Directed reachability from `origin` plus whole-graph topology counts.

    Topology only: it reports which nodes a walk can reach, never which habitat,
    food source, or movement is biologically plausible.
    """
    if origin not in graph:
        raise ValueError(f"origin node {origin!r} is not in graph")
    reachable = nx.descendants(graph, origin) | {str(origin)}
    return {
        "origin_node_id": str(origin),
        "reachable_nodes": len(reachable),
        "total_nodes": int(graph.number_of_nodes()),
        "reachable_edges": int(graph.subgraph(reachable).number_of_edges()),
        "total_edges": int(graph.number_of_edges()),
        "component_count": nx.number_weakly_connected_components(graph),
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
