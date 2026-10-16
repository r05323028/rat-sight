"""Constants for the Taipei stormwater infrastructure reference layer.

Stormwater geometry is infrastructure reference data. It is not rodent
observation data, inferred connectivity, traversability, or risk, and it carries
a separate ``data_class`` from the epistemic ``classification`` axis.
"""

from __future__ import annotations

STORMWATER_DATA_CLASS = "INFRASTRUCTURE_REFERENCE"
STORMWATER_CLASSIFICATION = "UNVERIFIED"

SOURCE_CRS = "EPSG:3826"
TARGET_CRS = "EPSG:4326"

# Bounded viewport query: EPSG:4326 degrees, max width/height per request.
BBOX_MAX_SPAN = 0.30
FEATURE_CAP = 5000
LON_MIN, LON_MAX = -180.0, 180.0
LAT_MIN, LAT_MAX = -90.0, 90.0

# Documented Candidate B identity (Evidence ID EVID-TPE-STORMWATER-NETWORK-2026-10-16).
OFFICIAL_DATASET_ID = "97b82d58-faba-4ee4-9488-dd5d04a79efd"
OFFICIAL_RESOURCE_ID = "5240223d-5187-454e-b323-63443a195639"
OFFICIAL_RESOURCE_VERSION = "2026-02-23T17:10:41Z"
OFFICIAL_ARCHIVE_SHA256 = "5d2ea04f7d032d21b07066310e80eb64a34ce8916b4a0c786b10948aeb4e10e4"
OFFICIAL_SOURCE_URL = "https://data.taipei/dataset/detail?id=97b82d58-faba-4ee4-9488-dd5d04a79efd"
OFFICIAL_DOWNLOAD_URL = (
    "https://data.taipei/api/frontstage/tpeod/dataset/resource.download"
    "?rid=5240223d-5187-454e-b323-63443a195639"
)
OFFICIAL_LICENSE = "政府資料開放授權條款-第1版 (https://data.gov.tw/license)"
OFFICIAL_ATTRIBUTION = "臺北市政府工務局"
REFERENCE_ONLY_WARNING = (
    "publisher states the network map is for reference only and exact data should be "
    "obtained from the relevant utility agency"
)

# Source XML tag (local name) -> public API property name. Order defines the
# public allowlist; every field is a nullable string preserving lexical source
# values.
SOURCE_ATTRIBUTE_MAP: tuple[tuple[str, str], ...] = (
    ("category_code", "類別碼"),
    ("pipe_number", "管線編號"),
    ("start_node_id", "起點編號"),
    ("end_node_id", "終點編號"),
    ("managing_unit", "管理單位"),
    ("work_category", "作業區分"),
    ("installation_date", "設置日期"),
    ("dimension_unit", "尺寸單位"),
    ("diameter_width", "管徑寬度"),
    ("diameter_height", "管徑高度"),
    ("conduit_count", "涵管條數"),
    ("material", "管線材料"),
    ("start_burial_depth", "起點埋設深度"),
    ("end_burial_depth", "終點埋設深度"),
    ("length", "管線長度"),
    ("pipe_type", "管線型態"),
    ("use_status", "使用狀態"),
    ("data_status", "資料狀態"),
    ("notes", "備註"),
)
SOURCE_ATTRIBUTE_NAMES: tuple[str, ...] = tuple(name for name, _ in SOURCE_ATTRIBUTE_MAP)

SOURCE_RECORD_ID_TAG = "識別碼"
PIPE_NUMBER_TAG = "管線編號"
START_NODE_TAG = "起點編號"
END_NODE_TAG = "終點編號"
NOTES_TAG = "備註"
PIPELINE_RECORD_TAG = "UTL_管線"
