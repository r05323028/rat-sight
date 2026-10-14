"""Explicit CRS parsing and coordinate transformations."""

from __future__ import annotations

import geopandas as gpd
import numpy as np
from numpy.typing import NDArray
from pyproj import CRS, Transformer
from shapely import transform as transform_coordinates
from shapely.geometry.base import BaseGeometry

type CRSLike = str | int | CRS
SUPPORTED_CRS = {"EPSG:4326", "EPSG:3826"}


def parse_crs(value: CRSLike) -> CRS:
    """Parse an explicit CRS; raise pyproj's ValueError for unknown definitions."""
    crs = CRS.from_user_input(value)
    return crs


def transform_geometry(
    geometry: BaseGeometry,
    source_crs: CRSLike,
    target_crs: CRSLike,
) -> BaseGeometry:
    """Transform geometry coordinates using x/y order regardless of CRS axis metadata."""
    if geometry is None:
        raise ValueError("geometry must not be None")
    source = parse_crs(source_crs)
    target = parse_crs(target_crs)
    transformer = Transformer.from_crs(source, target, always_xy=True)

    def project_coordinates(
        coordinates: NDArray[np.float64],
    ) -> NDArray[np.float64]:
        x = coordinates[:, 0]
        y = coordinates[:, 1]
        if coordinates.shape[1] == 3:
            transformed_x, transformed_y, transformed_z = transformer.transform(
                x, y, coordinates[:, 2]
            )
            return np.asarray(
                np.column_stack((transformed_x, transformed_y, transformed_z)),
                dtype=np.float64,
            )
        transformed_x, transformed_y = transformer.transform(x, y)
        return np.asarray(
            np.column_stack((transformed_x, transformed_y)),
            dtype=np.float64,
        )

    return transform_coordinates(geometry, project_coordinates, include_z=geometry.has_z)


def transform_geodataframe(
    frame: gpd.GeoDataFrame,
    target_crs: CRSLike,
) -> gpd.GeoDataFrame:
    """Reproject a GeoDataFrame only when its source CRS is explicit."""
    if frame.crs is None:
        raise ValueError("source GeoDataFrame must declare a CRS")
    target = parse_crs(target_crs)
    return frame.to_crs(target)
