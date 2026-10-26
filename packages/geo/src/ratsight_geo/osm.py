"""Small, strict OSM XML surface-network adapter."""

from __future__ import annotations

import hashlib
import os
from collections import Counter
from itertools import pairwise
from pathlib import Path
from xml.etree import ElementTree

import networkx as nx

DEFAULT_OSM_SOURCE = Path.home() / ".local/share/ratsight/network/taipei-songshan-20261023.osm"
EXPECTED_SHA256 = "faae4ffd1bd42e57871bdedbfdcc6e82b3324a458db95034d4ec40f0a019e67e"
OSM_SOURCE_URL = "https://api.openstreetmap.org/api/0.6/map?bbox=121.528,25.028,121.532,25.032"


def load_osm_surface_graph(path: str | Path | None = None) -> nx.MultiDiGraph:
    """Parse highway ways using shared OSM nodes as the only connectivity."""
    source = Path(path or os.environ.get("RATSIGHT_OSM_SOURCE", DEFAULT_OSM_SOURCE))
    if not source.is_file():
        raise FileNotFoundError(f"configured OSM source is absent: {source}")
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    if digest != EXPECTED_SHA256:
        raise ValueError(f"OSM source sha256 mismatch: expected {EXPECTED_SHA256}, got {digest}")

    root = ElementTree.parse(source).getroot()
    nodes = {
        element.attrib["id"]: (float(element.attrib["lon"]), float(element.attrib["lat"]))
        for element in root.findall("node")
    }
    ways: list[tuple[str, list[str], dict[str, str]]] = []
    for way in root.findall("way"):
        tags = {tag.attrib["k"]: tag.attrib["v"] for tag in way.findall("tag")}
        refs = [nd.attrib["ref"] for nd in way.findall("nd")]
        if tags.get("highway") and len(refs) >= 2 and all(ref in nodes for ref in refs):
            ways.append((way.attrib["id"], refs, tags))

    shared = Counter(ref for _, refs, _ in ways for ref in refs)
    graph = nx.MultiDiGraph(
        classification="SIMULATED",
        source_type="osm_surface_network",
        source_id=source.name,
        source_sha256=digest,
        source_crs="EPSG:4326",
        source_url=OSM_SOURCE_URL,
        resource_version="2026-10-23T10:08:00Z",
        license="ODbL 1.0",
        attribution="© OpenStreetMap contributors",
        coverage="EPSG:4326 bbox 121.528,25.028,121.532,25.032",
    )
    for way_id, refs, tags in ways:
        split = (
            [0]
            + [index for index, ref in enumerate(refs[1:-1], 1) if shared[ref] > 1]
            + [len(refs) - 1]
        )
        for index, (start, end) in enumerate(pairwise(split)):
            segment = refs[start : end + 1]
            source_id = f"{way_id}:{index}"
            geometry = tuple(nodes[ref] for ref in segment)
            for ref in (segment[0], segment[-1]):
                graph.add_node(
                    ref, coordinates=nodes[ref], classification="SIMULATED", source_id=ref
                )
            attributes = {
                "edge_id": source_id,
                "source_id": way_id,
                "movement_weight": 1.0,
                "geometry": geometry,
                "layer": "osm_surface",
                "classification": "SIMULATED",
                "source_crs": "EPSG:4326",
                "source_sha256": digest,
                "highway": tags["highway"],
                "oneway": tags.get("oneway", "no"),
            }
            direction = tags.get("oneway", "no")
            if direction != "-1":
                graph.add_edge(segment[0], segment[-1], key=source_id, **attributes)
            if direction in {"no", "", "0"} or direction not in {"yes", "true", "1", "-1"}:
                reverse = dict(attributes)
                reverse["edge_id"] = f"{source_id}:reverse"
                reverse["geometry"] = tuple(reversed(geometry))
                graph.add_edge(segment[-1], segment[0], key=reverse["edge_id"], **reverse)
            elif direction == "-1":
                reverse = dict(attributes)
                reverse["edge_id"] = f"{source_id}:reverse"
                reverse["geometry"] = tuple(reversed(geometry))
                graph.add_edge(segment[-1], segment[0], key=reverse["edge_id"], **reverse)
    return graph
