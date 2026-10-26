from pathlib import Path

from ratsight_geo.osm import EXPECTED_SHA256, load_osm_surface_graph

SOURCE = Path.home() / ".local/share/ratsight/network/taipei-songshan-20261023.osm"


def test_pinned_osm_graph_preserves_bent_geometry_and_provenance() -> None:
    graph = load_osm_surface_graph(SOURCE)
    assert graph.graph["source_sha256"] == EXPECTED_SHA256
    geometries = [data["geometry"] for *_, data in graph.edges(data=True)]
    assert any(len(geometry) > 2 for geometry in geometries)
    assert all(data["classification"] == "SIMULATED" for *_, data in graph.edges(data=True))
    assert all(data["source_crs"] == "EPSG:4326" for *_, data in graph.edges(data=True))
    edge_ids = [data["edge_id"] for *_, data in graph.edges(data=True)]
    assert len(edge_ids) == len(set(edge_ids))


def test_one_way_edges_have_no_reverse_transition() -> None:
    graph = load_osm_surface_graph(SOURCE)
    one_way = [
        (source, target, data)
        for source, target, data in graph.edges(data=True)
        if data["oneway"] == "yes"
    ]
    assert one_way
    assert all(
        not graph.has_edge(target, source, key=f"{data['edge_id']}:reverse")
        for source, target, data in one_way
    )


def test_missing_external_source_fails_clearly(tmp_path: Path) -> None:
    missing = tmp_path / "missing.osm"
    try:
        load_osm_surface_graph(missing)
    except FileNotFoundError as exc:
        assert "configured OSM source is absent" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("missing source must fail")
