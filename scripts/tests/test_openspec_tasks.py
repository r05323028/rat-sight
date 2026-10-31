from __future__ import annotations

import pytest

from scripts.openspec_tasks import TaskCounts, task_counts


def test_counts_only_required_checkboxes() -> None:
    text = "# Tasks\n\n## 1. Work\n\n- [x] 1.1 Done.\n- [ ] 1.2 Open.\n"
    counts = task_counts(text)
    assert counts == TaskCounts(done=1, total=2, excluded_unfinished=0)
    assert not counts.complete


def test_excluded_unchecked_checkbox_is_reported() -> None:
    text = "# Tasks\n\n## 1. Work\n\n- [x] 1.1 Done.\n\n## Out of Scope\n\n- [ ] hidden work\n"
    counts = task_counts(text)
    assert counts == TaskCounts(done=1, total=1, excluded_unfinished=1)
    assert not counts.complete


def test_excluded_plain_bullets_and_checked_boxes_do_not_count() -> None:
    text = (
        "# Tasks\n\n## 1. Work\n\n- [x] 1.1 Done.\n\n"
        "## Workflow follow-up\n\n- Archive after acceptance.\n- [x] 9.9 Already done.\n"
    )
    counts = task_counts(text)
    assert counts == TaskCounts(done=1, total=1, excluded_unfinished=0)
    assert counts.complete


def test_zero_tasks_is_not_complete() -> None:
    assert not task_counts("# Tasks\n\nNo checkboxes.\n").complete


@pytest.mark.parametrize(
    ("marker", "done", "nonstandard"),
    [(" ", 0, 0), ("x", 1, 0), ("X", 1, 0), ("~", 0, 1), ("-", 0, 1), ("", 0, 0)],
)
def test_only_x_completes_a_task(marker: str, done: int, nonstandard: int) -> None:
    counts = task_counts(f"# Tasks\n\n## 1. Work\n\n- [{marker}] 1.1 Work.\n")
    assert counts == TaskCounts(done=done, total=1, nonstandard=nonstandard)
    assert counts.complete is (done == 1)


def test_mixed_markers_are_all_counted() -> None:
    text = (
        "# Tasks\n\n## 1. Work\n\n"
        "- [ ] 1.1 Open.\n- [x] 1.2 Done.\n- [X] 1.3 Done.\n"
        "- [~] 1.4 Skipped.\n- [-] 1.5 Removed.\n- [] 1.6 Missing.\n"
    )
    counts = task_counts(text)
    assert counts == TaskCounts(done=2, total=6, nonstandard=2)
    assert not counts.complete


def test_bracketed_prose_is_not_a_checkbox() -> None:
    text = "# Tasks\n\n- [API] Document the endpoint.\n- [ ] 1.1 Real task.\n"
    assert task_counts(text) == TaskCounts(done=0, total=1)
