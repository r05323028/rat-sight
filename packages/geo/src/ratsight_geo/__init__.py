"""CRS-aware spatial utilities; never infer missing source CRS."""

from ratsight_geo.crs import transform_geodataframe, transform_geometry
from ratsight_geo.geometry import normalize_geodataframe, normalize_geometry

__all__ = [
    "normalize_geometry",
    "normalize_geodataframe",
    "transform_geodataframe",
    "transform_geometry",
]
