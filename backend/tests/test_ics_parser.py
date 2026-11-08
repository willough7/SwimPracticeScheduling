"""Tests for app/ics_parser.py.

They use small made-up calendars in tests/fixtures/ instead of a real
student's schedule (real .ics files are gitignored because they hold
student data). sample_schedule.ics covers the week of Mon 2026-11-09:

    Mon 11/9   CS 101    9:00-9:50     weekly MWF, DTEND
    Tue 11/10  MATH 210  1:00-2:15 pm  weekly TU/TH, DURATION instead of DTEND
    Wed 11/11  CS 101    9:00-9:50     (+ an all-day holiday that must be skipped)
    Thu 11/12  MATH 210  1:00-2:15 pm
    Thu 11/12  Advising  3:00-3:30 pm  stored in UTC (20:00Z)
    Fri 11/13  no CS 101: cancelled with EXDATE
    Fri 11/20  Exam Review             next week, must not appear
"""

from datetime import date, datetime
from pathlib import Path

from app.ics_parser import LOCAL_TZ, busy_blocks_for_week, load_calendar, monday_of
from app.intervals import overlapChecker

FIXTURES = Path(__file__).parent / "fixtures"
WEEK_OF_NOV_9 = date(2026, 11, 9)


def local(month, day, hour, minute=0):
    """Shorthand for a 2026 datetime in Indianapolis time."""
    return datetime(2026, month, day, hour, minute, tzinfo=LOCAL_TZ)


def sample_week():
    calendar = load_calendar(FIXTURES / "sample_schedule.ics")
    return busy_blocks_for_week(calendar, WEEK_OF_NOV_9)


# ---------- monday_of ----------

def test_monday_of_midweek_date():
    assert monday_of(date(2026, 11, 11)) == date(2026, 11, 9)   # Wednesday


def test_monday_of_a_monday_is_itself():
    assert monday_of(date(2026, 11, 9)) == date(2026, 11, 9)


def test_monday_of_sunday_goes_back_not_forward():
    # Python weeks run Monday-Sunday, so Sunday belongs to the week before.
    assert monday_of(date(2026, 11, 15)) == date(2026, 11, 9)


def test_monday_of_crosses_month_boundary():
    assert monday_of(date(2026, 11, 1)) == date(2026, 10, 26)   # Sunday Nov 1


# ---------- busy_blocks_for_week ----------

def test_full_week_matches_expected_blocks():
    assert sample_week() == [
        (local(11, 9, 9), local(11, 9, 9, 50)),
        (local(11, 10, 13), local(11, 10, 14, 15)),
        (local(11, 11, 9), local(11, 11, 9, 50)),
        (local(11, 12, 13), local(11, 12, 14, 15)),
        (local(11, 12, 15), local(11, 12, 15, 30)),
    ]


def test_blocks_are_start_end_pairs():
    # overlapChecker unpacks (start, end), so each block must have exactly 2 items.
    assert all(len(block) == 2 for block in sample_week())


def test_blocks_are_sorted_by_start():
    blocks = sample_week()
    assert blocks == sorted(blocks)


def test_all_day_events_are_skipped():
    # The holiday on Wed 11/11 has no time, so only CS 101 should show up that day.
    wednesday = [b for b in sample_week() if b[0].date() == date(2026, 11, 11)]
    assert wednesday == [(local(11, 11, 9), local(11, 11, 9, 50))]


def test_duration_is_used_when_there_is_no_dtend():
    tuesday = [b for b in sample_week() if b[0].date() == date(2026, 11, 10)]
    assert tuesday == [(local(11, 10, 13), local(11, 10, 14, 15))]


def test_utc_times_are_converted_to_local():
    # 20:00 UTC is 3:00 pm in Indianapolis in November (EST, UTC-5).
    starts = [start for start, _ in sample_week()]
    assert local(11, 12, 15) in starts


def test_cancelled_class_is_not_included():
    friday = [b for b in sample_week() if b[0].date() == date(2026, 11, 13)]
    assert friday == []


def test_events_from_other_weeks_are_not_included():
    assert all(WEEK_OF_NOV_9 <= start.date() <= date(2026, 11, 15)
               for start, _ in sample_week())


def test_every_block_has_a_timezone():
    # Naive and timezone-aware datetimes can't be compared. If any block came
    # back naive, comparing it to a practice time would crash.
    assert all(start.tzinfo is not None and end.tzinfo is not None
               for start, end in sample_week())


def test_floating_times_are_treated_as_local():
    # Some calendar apps export times with no timezone at all ("floating").
    # Those should be read as local time, the same as everything else.
    calendar = load_calendar(FIXTURES / "floating_times.ics")
    blocks = busy_blocks_for_week(calendar, WEEK_OF_NOV_9)
    assert blocks == [(local(11, 10, 10), local(11, 10, 11))]


# ---------- parser + overlapChecker together ----------

def test_parser_output_works_with_overlap_checker():
    blocks = sample_week()
    # Tuesday 1:30 pm practice runs into MATH 210 -> conflict.
    assert overlapChecker(blocks, (local(11, 10, 13, 30), local(11, 10, 15))) is True
    # Tuesday 6:00 am practice is clear.
    assert overlapChecker(blocks, (local(11, 10, 6), local(11, 10, 8))) is False
