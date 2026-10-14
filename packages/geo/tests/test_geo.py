from __future__ import annotations

import geopandas as gpd
import pytest
from pyproj import CRS
from ratsight_geo.crs import transform_geometry
from ratsight_geo.geometry import normalize_geodataframe, normalize_geometry
from shapely.geometry import Point, Polygon


def test_epsg_4326_round_trip_through_twd97() -> None:
    original = Point(121.5, 25.0)
    projected = transform_geometry(original, "EPSG:4326", "EPSG:3826")
    assert isinstance(projected, Point)
    restored = transform_geometry(projected, 3826, CRS.from_epsg(4326))
    assert isinstance(restored, Point)
    assert restored.x == pytest.approx(original.x, abs=1e-7)
    assert restored.y == pytest.approx(original.y, abs=1e-7)
    assert projected.x > 0 and projected.y > 0


def test_invalid_geometry_is_repaired() -> None:
    bow_tie = Polygon([(0, 0), (1, 1), (1, 0), (0, 1), (0, 0)])
    assert not bow_tie.is_valid
    repaired = normalize_geometry(bow_tie)
    assert repaired.is_valid
    assert not repaired.is_empty


def test_null_geometry_is_rejected() -> None:
    with pytest.raises(ValueError, match="geometry must not be None"):
        normalize_geometry(None)


def test_empty_geodataframe_keeps_explicit_target_crs() -> None:
    empty = gpd.GeoDataFrame(geometry=gpd.GeoSeries([], crs="EPSG:3826"))
    normalized = normalize_geodataframe(empty)
    assert normalized.empty
    assert normalized.crs == CRS.from_epsg(4326)


def test_missing_source_crs_is_not_guessed() -> None:
    frame = gpd.GeoDataFrame(geometry=[Point(0, 0)])
    with pytest.raises(ValueError, match="must declare a CRS"):
        normalize_geodataframe(frame)
