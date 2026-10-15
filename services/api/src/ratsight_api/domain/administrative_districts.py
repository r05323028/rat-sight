"""Constants and validation envelopes for administrative reference boundaries.

Administrative reference geometry is not biological or infrastructure evidence.
It carries a separate ``data_class`` and stays off the epistemic
``Classification`` axis except for an explicit ``UNVERIFIED`` currentness value.
"""

from __future__ import annotations

ADMINISTRATIVE_DATA_CLASS = "ADMINISTRATIVE_REFERENCE"
DISTRICT_CLASSIFICATION = "UNVERIFIED"
PROVENANCE_SCHEMA_VERSION = "1"

SOURCE_CRS = "EPSG:3826"
TARGET_CRS = "EPSG:4326"

# Deterministic margin envelopes used only to catch CRS/axis mistakes, not to
# assert an expected district count. Source: observed 2022-09-15 resource bounds
# in EPSG:3826; target: the transformed EPSG:4326 bounds. A 1 km source margin
# and ~0.01 degree consumer margin were applied around those observed bounds.
SOURCE_ENVELOPE = (296000.0, 2761000.0, 317500.0, 2790000.0)
TARGET_ENVELOPE = (121.45, 24.94, 121.70, 25.23)

DISTRICT_ID_ATTRIBUTE = "CPID"
DISTRICT_NAME_ATTRIBUTE = "TNAME"
