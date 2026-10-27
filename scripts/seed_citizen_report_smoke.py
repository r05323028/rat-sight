"""Seed deterministic isolated 250 m cells for the citizen-origin browser smoke test.

These rows are SIMULATED software fixtures, not citizen reports: they carry no
report counts, no Rat Radar identity, and no observation claims. The seed only
runs when the explicit smoke dataset and opt-in flag are set.
"""

import hashlib
import os
from json import dumps

from geoalchemy2.shape import from_shape
from pyproj import Transformer
from ratsight_api.domain.citizen_report_aggregates import (
    DATASET_ID,
    SYNTHETIC_FIXTURE_CLASSIFICATION,
    SYNTHETIC_FIXTURE_DATA_CLASS,
    SYNTHETIC_FIXTURE_NOTICE,
    synthetic_aggregate_fixture_enabled,
)
from ratsight_api.infrastructure.database.connection import SessionLocal
from ratsight_api.infrastructure.database.models import CitizenReportCell
from ratsight_geo.osm import DEFAULT_OSM_SOURCE, EXPECTED_SHA256, load_osm_surface_graph
from shapely.geometry import Polygon
from sqlalchemy import delete, insert, text

CELL_SIZE_METERS = 250
MIN_CELL_SEPARATION_METERS = 500
MONTH = "2026-01"
REPORT_TYPE = "sighting"
RESOURCE_VERSION = "smoke-fixture-v1"
MAP_CENTER = (121.5654, 25.033)
REFERENCE_SOURCE_ID = DEFAULT_OSM_SOURCE.name
TRANSFORMER = Transformer.from_crs("EPSG:3826", "EPSG:4326", always_xy=True)
PROJECT_TO_TWD97 = Transformer.from_crs("EPSG:4326", "EPSG:3826", always_xy=True)


def _cell_polygon(longitude: float, latitude: float) -> Polygon:
    """Return a 250 m square around an OSM node, stored in EPSG:4326."""
    x, y = PROJECT_TO_TWD97.transform(longitude, latitude)
    half = CELL_SIZE_METERS / 2
    x_coordinates = [x - half, x + half, x + half, x - half, x - half]
    y_coordinates = [y - half, y - half, y + half, y + half, y - half]
    return Polygon(
        [
            TRANSFORMER.transform(x_coord, y_coord)
            for x_coord, y_coord in zip(x_coordinates, y_coordinates, strict=True)
        ]
    )


def _selected_nodes(graph):
    """Pick the nearest node to the map center and a visibly separated second one."""
    nodes = [
        (data["coordinates"][0], data["coordinates"][1], str(node_id))
        for node_id, data in graph.nodes(data=True)
    ]

    def distance(item: tuple[float, float, str], origin: tuple[float, float]) -> float:
        return (item[0] - origin[0]) ** 2 + (item[1] - origin[1]) ** 2

    nearest = min(nodes, key=lambda item: distance(item, MAP_CENTER))

    def separation(item: tuple[float, float, str]) -> float:
        return distance(item, (nearest[0], nearest[1]))

    # Adjacent OSM nodes can be only metres apart, which produces overlapping
    # markers. Pick a second node far enough to exercise marker selection.
    separated = next(
        (
            node
            for node in sorted(nodes, key=separation)
            if node[2] != nearest[2]
            and separation(node) >= (MIN_CELL_SEPARATION_METERS / 111_320) ** 2
        ),
        None,
    )
    if separated is None:
        raise SystemExit("no second OSM node is separated enough for the smoke fixture")
    return [nearest, separated]


def _provenance(content_sha256: str) -> dict[str, object]:
    return {
        "schema_version": "1",
        "source_kind": "synthetic_aggregate_fixture",
        "dataset_id": DATASET_ID,
        "resource_version": RESOURCE_VERSION,
        "content_sha256": content_sha256,
        "reference_source_id": REFERENCE_SOURCE_ID,
        "reference_source_sha256": EXPECTED_SHA256,
        "source_crs": "EPSG:4326",
        "target_crs": "EPSG:4326",
        "cell_size_meters": CELL_SIZE_METERS,
        "test_scope": "isolated_disposable_postgis_smoke",
        "synthetic": True,
        "note": SYNTHETIC_FIXTURE_NOTICE,
    }


def main() -> None:
    if not synthetic_aggregate_fixture_enabled():
        raise SystemExit(
            "refusing synthetic citizen fixture seed: set "
            "RATSIGHT_ENABLE_SYNTHETIC_AGGREGATE_FIXTURE=1 and "
            "RATSIGHT_CITIZEN_REPORT_DATASET_ID=ratsight-smoke-<name>"
        )
    with SessionLocal() as session, session.begin():
        # Aggregates are immutable after import. This is a smoke-only reset of
        # synthetic fixture rows: disable the row trigger transactionally, delete
        # only this fixture dataset, then re-enable it. A rollback restores it.
        session.execute(
            text("ALTER TABLE citizen_report_cells DISABLE TRIGGER citizen_report_cells_immutable")
        )
        session.execute(delete(CitizenReportCell).where(CitizenReportCell.dataset_id == DATASET_ID))
        session.execute(
            text("ALTER TABLE citizen_report_cells ENABLE TRIGGER citizen_report_cells_immutable")
        )
        if os.environ.get("SMOKE_EMPTY") == "1":
            print("cleared synthetic citizen-report smoke fixture")
            return
        graph = load_osm_surface_graph()
        cells = []
        for index, (longitude, latitude, node_id) in enumerate(_selected_nodes(graph), start=1):
            polygon = _cell_polygon(longitude, latitude)
            cells.append(
                {
                    "cell_id": f"smoke-cell-{index}",
                    "node_id": node_id,
                    "polygon": polygon,
                }
            )
        spec = [
            {"cell_id": cell["cell_id"], "node_id": cell["node_id"], "wkt": cell["polygon"].wkt}
            for cell in cells
        ]
        content_sha256 = hashlib.sha256(dumps(spec, sort_keys=True).encode()).hexdigest()
        provenance = _provenance(content_sha256)
        session.execute(
            insert(CitizenReportCell),
            [
                {
                    "dataset_id": DATASET_ID,
                    "resource_version": RESOURCE_VERSION,
                    "content_sha256": content_sha256,
                    "data_class": SYNTHETIC_FIXTURE_DATA_CLASS,
                    "classification": SYNTHETIC_FIXTURE_CLASSIFICATION,
                    "cell_id": cell["cell_id"],
                    "month": MONTH,
                    "report_type": REPORT_TYPE,
                    "report_count": None,
                    "provenance": provenance,
                    "geometry": from_shape(cell["polygon"], srid=4326),
                }
                for cell in cells
            ],
        )
    print("seeded synthetic citizen-report smoke fixture")
    for cell in cells:
        print(f"  {cell['cell_id']} at OSM node {cell['node_id']}")


if __name__ == "__main__":
    main()
