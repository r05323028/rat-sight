"""Prepare a directed, layered graph from explicitly identified edge records."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

import networkx as nx


def build_spatial_graph(
    edge_records: Iterable[Mapping[str, Any]],
) -> nx.MultiDiGraph:
    """Build graph edges from normalized records; topology is never inferred from proximity."""
    graph = nx.MultiDiGraph()
    for record in edge_records:
        source = str(record["source"])
        target = str(record["target"])
        weight = float(record["movement_weight"])
        if weight <= 0:
            raise ValueError("movement_weight must be positive")
        graph.add_edge(
            source,
            target,
            key=str(record.get("edge_id", f"{source}:{target}")),
            movement_weight=weight,
            layer=str(record.get("layer", "unspecified")),
            source_classification=str(record.get("classification", "UNVERIFIED")),
        )
    return graph
