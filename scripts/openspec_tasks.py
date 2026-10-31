"""Shared task-progress counting for OpenSpec changes.

Both the quality gate and the owner-acceptance CLI must agree on what counts as a
required task. Every checkbox-like marker is counted: only `[x]` and `[X]` are
complete, and `[ ]`, `[]`, `[~]`, `[-]` and similar markers are unfinished or
invalid work. Unchecked markers under an excluded heading ("Out of Scope",
"Future follow-up", "Non-goals", "Not required") are reported instead of ignored:
silently dropping them is how unfinished work disappears from a review.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# A checkbox marker holds at most three characters, so bracketed prose such as
# "- [API] endpoint" stays a plain bullet that OpenSpec does not track.
CHECKBOX = re.compile(r"^\s*[-*+] \[([^\]]{0,3})\](?!\()")
MARKER = re.compile(r"[ xX~\-/>!?*.]*")
HEADING = re.compile(r"^\s*#{1,6}\s+(.+?)\s*#*\s*$")
EXCLUDED_HEADING = re.compile(
    r"\b(?:non[- ]?goals?|future follow[- ]?ups?|workflow follow[- ]?ups?"
    r"|out of scope|not required)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class TaskCounts:
    done: int = 0
    total: int = 0
    excluded_unfinished: int = 0
    nonstandard: int = 0

    @property
    def complete(self) -> bool:
        return self.total > 0 and self.done == self.total and self.excluded_unfinished == 0


def is_done_marker(marker: str) -> bool:
    return marker.strip().lower() == "x"


def task_counts(text: str) -> TaskCounts:
    """Count required checkboxes and report unchecked checkboxes in excluded sections.

    Excluded sections may hold plain bullets (the upstream "workflow follow-up"
    convention) but not unfinished checkboxes, which would otherwise be hidden work.
    Ground truth comes from the marker text alone; no other marker can complete a task.
    """
    done = total = excluded_unfinished = nonstandard = 0
    excluded = False
    for line in text.splitlines():
        heading = HEADING.match(line)
        if heading:
            excluded = bool(EXCLUDED_HEADING.search(heading.group(1)))
            continue
        checkbox = CHECKBOX.match(line)
        if not checkbox:
            continue
        marker = checkbox.group(1)
        if not MARKER.fullmatch(marker):
            continue
        complete = is_done_marker(marker)
        if not complete and marker.strip():
            nonstandard += 1
        if excluded:
            if not complete:
                excluded_unfinished += 1
            continue
        total += 1
        if complete:
            done += 1
    return TaskCounts(
        done=done,
        total=total,
        excluded_unfinished=excluded_unfinished,
        nonstandard=nonstandard,
    )
