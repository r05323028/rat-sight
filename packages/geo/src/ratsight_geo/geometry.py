"""Geometry validation and normalization."""

from __future__ import annotations

import geopandas as gpd
from pyproj import CRS
from shapely import make_valid
from shapely.geometry.base import BaseGeometry

from ratsight_geo.crs import CRSLike


def normalize_geometry(geometry: BaseGeometry | None) -> BaseGeometry:
    """Repair invalid geometry without guessing CRS or silently dropping empties."""
    if geometry is None:
        raise ValueError("geometry must not be None")
    if geometry.is_empty or geometry.is_valid:
        return geometry
    repaired = make_valid(geometry)
    if not repaired.is_valid:
        raise ValueError("geometry could not be made valid")
    return repaired


def normalize_geodataframe(
    frame: gpd.GeoDataFrame,
    target_crs: CRSLike = "EPSG:4326",
) -> gpd.GeoDataFrame:
    """Repair geometries and transform a frame to an explicit target CRS."""
    if frame.crs is None:
        raise ValueError("source GeoDataFrame must declare a CRS")
    if frame.geometry.name not in frame.columns:
        raise ValueError("GeoDataFrame must have an active geometry column")
    normalized = frame.copy()
    normalized.geometry = normalized.geometry.map(normalize_geometry)
    return normalized.to_crs(CRS.from_user_input(target_crs))
