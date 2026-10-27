from pathlib import Path

import networkx as nx
from ratsight_geo.osm import (
    DEFAULT_OSM_SOURCE,
    EXPECTED_SHA256,
    _parse_osm_surface_graph,
    load_osm_surface_graph,
)

SOURCE = DEFAULT_OSM_SOURCE


def test_pinned_osm_graph_preserves_bent_geometry_and_provenance() -> None:
    graph = load_osm_surface_graph(SOURCE)
    assert graph.graph["source_sha256"] == EXPECTED_SHA256
    geometries = [data["geometry"] for *_, data in graph.edges(data=True)]
    assert any(len(geometry) > 2 for geometry in geometries)
    assert all(data["classification"] == "SIMULATED" for *_, data in graph.edges(data=True))
    assert all(data["source_crs"] == "EPSG:4326" for *_, data in graph.edges(data=True))
    edge_ids = [data["edge_id"] for *_, data in graph.edges(data=True)]
    assert len(edge_ids) == len(set(edge_ids))


def test_vehicle_oneway_metadata_does_not_remove_reverse_movement() -> None:
    graph = load_osm_surface_graph(SOURCE)
    one_way = [
        (source, target, data)
        for source, target, data in graph.edges(data=True)
        if data["oneway"] in {"yes", "true", "1", "-1"} and not data["edge_id"].endswith(":reverse")
    ]
    assert one_way
    for source, target, data in one_way:
        reverse = graph.get_edge_data(target, source, key=f"{data['edge_id']}:reverse")
        assert reverse is not None
        assert reverse["oneway"] == data["oneway"]
        assert reverse["geometry"] == tuple(reversed(data["geometry"]))


def test_visual_crossings_without_shared_osm_nodes_remain_disconnected(
    tmp_path: Path,
) -> None:
    source = tmp_path / "crossing.osm"
    source.write_text(
        """<osm>
          <node id="n1" lon="0" lat="0"/>
          <node id="n2" lon="2" lat="2"/>
          <node id="n3" lon="0" lat="2"/>
          <node id="n4" lon="2" lat="0"/>
          <node id="n5" lon="3" lat="2"/>
          <way id="w1"><nd ref="n1"/><nd ref="n2"/>
            <tag k="highway" v="residential"/><tag k="oneway" v="yes"/>
          </way>
          <way id="w2"><nd ref="n3"/><nd ref="n4"/>
            <tag k="highway" v="residential"/><tag k="bridge" v="yes"/>
            <tag k="layer" v="1"/>
          </way>
          <way id="w3"><nd ref="n2"/><nd ref="n5"/>
            <tag k="highway" v="service"/>
          </way>
        </osm>""",
        encoding="utf-8",
    )
    graph = _parse_osm_surface_graph(
        str(source.resolve()), "fixture-digest", source.stat().st_mtime_ns
    )

    assert nx.has_path(graph.to_undirected(), "n1", "n5")
    assert not nx.has_path(graph.to_undirected(), "n1", "n3")
    assert not nx.has_path(graph.to_undirected(), "n1", "n4")
    assert all(data["coordinates"] != (1.0, 1.0) for _, data in graph.nodes(data=True))


def test_missing_external_source_fails_clearly(tmp_path: Path) -> None:
    missing = tmp_path / "missing.osm"
    try:
        load_osm_surface_graph(missing)
    except FileNotFoundError as exc:
        assert "configured OSM source is absent" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("missing source must fail")
