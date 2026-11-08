"""Tests for app/intervals.py.

These are the asserts from the __main__ block of intervals.py, moved into
pytest so they run with every other test. Plain numbers stand in for times
in most cases; the last tests use real timezone-aware datetimes, since that
is what the app actually passes in.
"""

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from app.intervals import mergeBlocks, overlapChecker

INDY = ZoneInfo("America/Indiana/Indianapolis")


# ---------- mergeBlocks ----------

@pytest.mark.parametrize(
    "blocks, expected",
    [
        ([], []),
        ([(9, 10)], [(9, 10)]),
        ([(9, 10), (11, 12)], [(9, 10), (11, 12)]),            # gap: stay separate
        ([(9, 11), (10, 12)], [(9, 12)]),                       # partial overlap
        ([(9, 10), (10, 11)], [(9, 11)]),                       # touching
        ([(13, 14), (9, 10)], [(9, 10), (13, 14)]),             # unsorted input
        ([(9, 12), (10, 11)], [(9, 12)]),                       # one inside another
        ([(9, 10), (9.5, 11), (10.5, 12)], [(9, 12)]),          # chain of overlaps
    ],
)
def test_merge_blocks(blocks, expected):
    assert mergeBlocks(blocks) == expected


def test_merge_blocks_does_not_modify_input():
    original = [(13, 14), (9, 10)]
    mergeBlocks(original)
    assert original == [(13, 14), (9, 10)]


# ---------- overlapChecker ----------

@pytest.mark.parametrize(
    "class_blocks, practice, expected",
    [
        ([(9, 11)], (15, 17), False),                    # class well before practice
        ([(15, 17)], (9, 11), False),                    # class well after practice
        ([(9, 11)], (11, 13), False),                    # class ends as practice starts
        ([(9, 11)], (7, 9), False),                      # practice ends as class starts
        ([(9, 11)], (1, 3), False),
        ([(9, 11), (15, 17), (9, 11)], (11, 13), False), # several classes, none clash
        ([(9, 16)], (11, 13), True),                     # practice inside class
        ([(9, 16)], (8, 13), True),                      # partial overlap
        ([(11.5, 12.5)], (11, 13), True),                # class inside practice
        ([(11, 13)], (11, 13), True),                    # identical times
        ([(11, 12)], (11, 13), True),                    # same start, class ends early
        ([], (11, 13), False),                           # swimmer with no classes
    ],
)
def test_overlap_checker(class_blocks, practice, expected):
    assert overlapChecker(class_blocks, practice) is expected


def test_overlap_checker_with_real_datetimes():
    # Same rule as above, but with the timezone-aware datetimes the
    # .ics parser actually produces.
    monday_class = (
        datetime(2026, 11, 9, 9, 0, tzinfo=INDY),
        datetime(2026, 11, 9, 9, 50, tzinfo=INDY),
    )
    clashing_practice = (
        datetime(2026, 11, 9, 9, 30, tzinfo=INDY),
        datetime(2026, 11, 9, 11, 0, tzinfo=INDY),
    )
    back_to_back_practice = (
        datetime(2026, 11, 9, 9, 50, tzinfo=INDY),
        datetime(2026, 11, 9, 11, 0, tzinfo=INDY),
    )
    assert overlapChecker([monday_class], clashing_practice) is True
    assert overlapChecker([monday_class], back_to_back_practice) is False


def test_same_clock_time_on_different_days_does_not_overlap():
    # A Monday 9am class must not gray a swimmer out of a Tuesday 9am practice.
    monday_class = (
        datetime(2026, 11, 9, 9, 0, tzinfo=INDY),
        datetime(2026, 11, 9, 10, 0, tzinfo=INDY),
    )
    tuesday_practice = (
        datetime(2026, 11, 10, 9, 0, tzinfo=INDY),
        datetime(2026, 11, 10, 10, 0, tzinfo=INDY),
    )
    assert overlapChecker([monday_class], tuesday_practice) is False
