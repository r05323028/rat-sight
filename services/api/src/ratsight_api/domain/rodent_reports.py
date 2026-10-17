"""Constants for the fixture-only rodent report layer.

Synthetic report-shaped fixtures are ``SIMULATED`` report events, not
observations, prevalence, population, movement, disease risk, or intervention
evidence. ``data_class`` is separate from the epistemic ``classification`` axis.
"""

from __future__ import annotations

RODENT_REPORT_DATA_CLASS = "RODENT_REPORT"
RODENT_REPORT_CLASSIFICATION = "SIMULATED"
SOURCE_KIND = "synthetic_fixture"

FIXTURE_DATASET_ID = "00000000-0000-4000-8000-000000000002"
FIXTURE_RESOURCE_VERSION = "2026-10-17T00:00:00Z"
FIXTURE_RETRIEVED_AT = "2026-10-17T00:00:00Z"
FIXTURE_SHA256 = "611b8f66f023f96b745fd0bd7b01943629400bf837ad45283bde5b835505080d"

BBOX_MAX_SPAN = 0.30
FEATURE_CAP = 5000
LON_MIN, LON_MAX = -180.0, 180.0
LAT_MIN, LAT_MAX = -90.0, 90.0

CSV_COLUMNS: tuple[str, ...] = (
    "source_record_id",
    "report_type",
    "reported_at",
    "longitude",
    "latitude",
    "location_precision",
    "review_status",
    "municipal_status",
    "action_status",
)

REPORT_TYPES = frozenset({"sighting_report", "nuisance_report", "service_request", "unknown"})
LOCATION_PRECISIONS = frozenset(
    {"synthetic_point", "coarse_grid_100m", "coarse_grid_1km", "unknown"}
)
REVIEW_STATUSES = frozenset({"unreviewed", "platform_moderated", "municipal_reviewed", "unknown"})
MUNICIPAL_STATUSES = frozenset({"not_assessed", "confirmed_by_authority", "rejected", "unknown"})
ACTION_STATUSES = frozenset({"none_reported", "inspection", "treatment", "unknown"})

FIXTURE_NOTICE = (
    "Synthetic fixture only. Not a rodent observation, prevalence, population, "
    "movement, disease-risk, or intervention record."
)
FIXTURE_ATTRIBUTION = "RatSight synthetic rodent-report fixture"
UNCERTAINTY_CURRENTNESS = (
    "Fixture timestamps are fixed synthetic values; no real reporting period is represented."
)
UNCERTAINTY_NOTE = (
    "Report-shaped synthetic records are SIMULATED and must not be interpreted as "
    "verified observations, infestation, prevalence, risk, or movement."
)
