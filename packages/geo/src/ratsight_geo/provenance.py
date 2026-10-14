"""Small provenance contract shared by geospatial transforms."""

from __future__ import annotations

from typing import Literal, TypedDict


class SpatialProvenance(TypedDict):
    classification: Literal["OBSERVED", "INFERRED", "SIMULATED", "UNVERIFIED"]
    source_id: str | None
    source_crs: str
    processing: str


def provenance_record(
    *,
    classification: Literal["OBSERVED", "INFERRED", "SIMULATED", "UNVERIFIED"],
    source_id: str | None,
    source_crs: str,
    processing: str,
) -> SpatialProvenance:
    """Create an explicit record; callers must supply source CRS and processing."""
    return {
        "classification": classification,
        "source_id": source_id,
        "source_crs": source_crs,
        "processing": processing,
    }
