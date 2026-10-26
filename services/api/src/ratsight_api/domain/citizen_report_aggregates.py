"""Constants for the aggregated public citizen-report layer.

Rows are counts of third-party citizen reports, coarsened to a 250 m grid and
month buckets, with cells below a suppression minimum dropped. They are
``UNVERIFIED`` citizen reports: not observations, prevalence, population,
movement, or disease-risk evidence, and never a simulation input.
"""

from __future__ import annotations

CITIZEN_REPORT_DATA_CLASS = "CITIZEN_REPORT_AGGREGATE"
CITIZEN_REPORT_CLASSIFICATION = "UNVERIFIED"
SOURCE_KIND = "public_citizen_report_export"
SOURCE_URL = "https://ratdar.taipei/"
ATTRIBUTION = "公民通報資料來源：見鼠雷達 ratdar.taipei（公開通報匯出，未經平台授權）"
LICENSE_NOTE = (
    "公開可讀取的公民通報匯出；無授權條款、無書面再利用同意。"
    "僅以聚合計數呈現，未驗證，不得視為觀測或再散布原始紀錄。"
)

CELL_SIZE_METERS = 250
SUPPRESSION_MINIMUM = 3
MONTH_TIMEZONE_ASSUMPTION = "Asia/Taipei wall-clock time in the export; UTC offset unverified"

DATASET_ID = "ratdar-taipei-public-export"
FEATURE_CAP = 5000
BBOX_MAX_SPAN = 0.30
# Taiwan main island bounds; the export also contains a few outlying reports.
LON_MIN, LON_MAX = 119.0, 122.6
LAT_MIN, LAT_MAX = 21.5, 25.5
MONTH_PATTERN = r"^\d{4}-(0[1-9]|1[0-2])$"

RAW_COLUMNS: tuple[str, ...] = (
    "通報時間",
    "類型",
    "地點",
    "狀態",
    "說明",
    "照片網址",
    "緯度",
    "經度",
)
DROPPED_COLUMNS: tuple[str, ...] = ("地點", "說明", "照片網址")

REPORT_TYPE_CODES = {"鼠蹤": "sighting", "毒餌": "bait_station"}
DEFAULT_REPORT_TYPE = "other"

NOTICE = (
    "公民通報聚合計數（250 公尺網格、按月），已抑制少於 "
    f"{SUPPRESSION_MINIMUM} 筆的網格與類型列。屬 UNVERIFIED 公民回報，"
    "不是觀測、盛行率、族群、移動或風險證據，也不作為模擬輸入。"
)
