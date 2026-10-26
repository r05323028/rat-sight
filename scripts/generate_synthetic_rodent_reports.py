"""Deterministically regenerate the synthetic rodent-report fixture.

The output is SIMULATED report-shaped data. It contains no record copied from
any real citizen-report export. Only three coarse things are informed by
aggregate statistics of the public Rat Radar export documented in
docs/evidence/ratdar-reuse-claim-2026-10-26.md: the report-type mix, the
monthly volume shape, and the time-of-day shape. Hotspot centres are chosen by
the author as plausible Taipei retail/nightlife areas; coordinates are jittered
synthetic points, not observed locations.

Usage:
    uv run python scripts/generate_synthetic_rodent_reports.py
    uv run python scripts/generate_synthetic_rodent_reports.py --write
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import random
from datetime import UTC, datetime, timedelta
from pathlib import Path

DESCRIPTION = "Regenerate the deterministic synthetic rodent-report fixture."
SEED = 20261026
RECORD_COUNT = 160
OUTPUT_PATH = (
    Path(__file__).resolve().parents[1]
    / "services/api/tests/fixtures/rodent_reports/synthetic_reports.csv"
)
HEADER = [
    "source_record_id",
    "report_type",
    "reported_at",
    "longitude",
    "latitude",
    "location_precision",
    "review_status",
    "municipal_status",
    "action_status",
]
CLASSIFICATION = {
    "location_precision": "synthetic_point",
    "review_status": "unreviewed",
    "municipal_status": "not_assessed",
    "action_status": "none_reported",
}
TYPE_WEIGHTS = {
    "sighting_report": 88,
    "nuisance_report": 9,
    "service_request": 2,
    "unknown": 1,
}
MONTH_WEIGHTS = {"2026-06": 30, "2026-07": 26, "2026-08": 22, "2026-09": 26, "2026-10": 24}
HOUR_WEIGHTS = {
    0: 1,
    1: 1,
    2: 1,
    3: 1,
    4: 1,
    5: 2,
    6: 4,
    7: 7,
    8: 8,
    9: 6,
    10: 5,
    11: 5,
    12: 4,
    13: 4,
    14: 4,
    15: 4,
    16: 5,
    17: 6,
    18: 9,
    19: 10,
    20: 10,
    21: 9,
    22: 7,
    23: 4,
}
HOTSPOTS = [
    ("萬華龍山寺周邊", 121.4995, 25.0370, 22, 0.0028),
    ("西門町周邊", 121.5060, 25.0430, 12, 0.0018),
    ("中山條通周邊", 121.5235, 25.0530, 18, 0.0024),
    ("雙連寧夏周邊", 121.5170, 25.0575, 14, 0.0020),
    ("大安永康周邊", 121.5305, 25.0300, 16, 0.0022),
    ("饒河街松山周邊", 121.5770, 25.0505, 12, 0.0020),
    ("公館周邊", 121.5335, 25.0150, 8, 0.0018),
    ("士林夜市周邊", 121.5240, 25.0880, 7, 0.0022),
    ("內湖西湖周邊", 121.5670, 25.0800, 5, 0.0030),
]
LON_BOUNDS = (121.4500, 121.6200)
LAT_BOUNDS = (24.9500, 25.1200)


def _weighted_hour(rng: random.Random) -> int:
    hours = list(HOUR_WEIGHTS)
    return rng.choices(hours, weights=[HOUR_WEIGHTS[hour] for hour in hours], k=1)[0]


def _weighted_type(rng: random.Random) -> str:
    types = list(TYPE_WEIGHTS)
    return rng.choices(types, weights=[TYPE_WEIGHTS[name] for name in types], k=1)[0]


def _timestamps(rng: random.Random) -> list[int]:
    total = sum(MONTH_WEIGHTS.values())
    denominators = RECORD_COUNT / total
    counts = {month: round(weight * denominators) for month, weight in MONTH_WEIGHTS.items()}
    counts[list(MONTH_WEIGHTS)[-1]] += RECORD_COUNT - sum(counts.values())
    stamps: list[int] = []
    for month, count in counts.items():
        year_text, month_text = month.split("-")
        year, month_number = int(year_text), int(month_text)
        start = datetime(year, month_number, 1, tzinfo=UTC)
        following = datetime(year + (month_number == 12), (month_number % 12) + 1, 1, tzinfo=UTC)
        span = int((following - start).total_seconds())
        for _ in range(count):
            reported = start + timedelta(seconds=rng.randrange(span))
            reported = reported.replace(
                hour=_weighted_hour(rng), minute=rng.randrange(60), second=0
            )
            stamps.append(int(reported.timestamp()))
    return sorted(stamps)


def build_rows() -> list[list[str]]:
    rng = random.Random(SEED)
    rows: list[list[str]] = []
    for index, stamp in enumerate(_timestamps(rng), start=1):
        _, lon, lat, _, sigma = rng.choices(HOTSPOTS, weights=[spot[3] for spot in HOTSPOTS], k=1)[
            0
        ]
        longitude = min(max(rng.gauss(lon, sigma), LON_BOUNDS[0]), LON_BOUNDS[1])
        latitude = min(max(rng.gauss(lat, sigma), LAT_BOUNDS[0]), LAT_BOUNDS[1])
        rows.append(
            [
                f"RR-{index:04d}",
                _weighted_type(rng),
                datetime.fromtimestamp(stamp, tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
                f"{longitude:.4f}",
                f"{latitude:.4f}",
                CLASSIFICATION["location_precision"],
                CLASSIFICATION["review_status"],
                CLASSIFICATION["municipal_status"],
                CLASSIFICATION["action_status"],
            ]
        )
    return rows


def write_fixture(path: Path = OUTPUT_PATH) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(HEADER)
        writer.writerows(build_rows())
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument("--write", action="store_true", help="overwrite the committed fixture")
    parser.add_argument("--path", type=Path, default=OUTPUT_PATH)
    args = parser.parse_args(argv)
    if not args.write:
        digest = hashlib.sha256()
        for row in [HEADER, *build_rows()]:
            digest.update((",".join(row) + "\n").encode("utf-8"))
        print(f"dry-run sha256={digest.hexdigest()} records={RECORD_COUNT}")
        return 0
    print(f"wrote {args.path} sha256={write_fixture(args.path)} records={RECORD_COUNT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
