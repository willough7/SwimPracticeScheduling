from datetime import date, time, datetime
import pytest

from pathlib import Path

from app.models import Practice, Day, Swimmer, WeightsGroup
from app.conflicts import (practice_block, has_conflict, conflicting_swimmers,
                           get_swimmers_status_for_practice)
from app.ics_parser import LOCAL_TZ

WEEK_START = date(year=2026,
                      month=11,
                      day=2)

def create_practice(**kwargs):
    defaults = dict(practice_id=1,
                  practice_title="Swim",
                  day=Day.TUESDAY,
                  start_time=time(13),
                  end_time=time(15),
                  is_morning=False)
    defaults.update(kwargs)
    return Practice(**defaults)

def create_class_block(start=8, start_min=0, end=9, end_min=0, on=WEEK_START):
    return (datetime.combine(on, time(start, start_min), tzinfo=LOCAL_TZ),
            datetime.combine(on, time(end, end_min), tzinfo=LOCAL_TZ))

def create_schedule(swimmers_ids=[1,2,3],
                    class_blocks=[[],[],[]]):
    schedule: dict[int, list[tuple[datetime, datetime]]] = dict()

    for swimmer_id, class_block in zip(swimmers_ids, class_blocks):
        schedule[swimmer_id] = class_block        

    return schedule




def test_tuesday_practice_is_on_tuesday():
    practice = create_practice()
    start, end = practice_block(practice, WEEK_START)

    assert start == datetime(2026, 11, 3, 13, 0, tzinfo=LOCAL_TZ)
    assert end == datetime(2026, 11, 3, 15, 0, tzinfo=LOCAL_TZ)

def test_sunday_practice_is_on_sunday():
    practice = create_practice(day=Day.SUNDAY)
    start, end = practice_block(practice, WEEK_START)

    assert start == datetime(2026, 11, 8, 13, 0, tzinfo=LOCAL_TZ)
    assert end == datetime(2026, 11, 8, 15, 0, tzinfo=LOCAL_TZ)

def test_sunday_practice_crosses_into_new_year():
    practice = create_practice(day=Day.SUNDAY)
    start, end = practice_block(practice, date(2026, 12, 28))
    assert start.date() == date(2027, 1, 3)

def test_monday_8am_conflict():
    practice = create_practice(day=Day.MONDAY,start_time=time(7),end_time=time(9))
    class_block = create_class_block(on=WEEK_START)
    assert has_conflict([class_block], practice, WEEK_START)

def test_class_ending_when_practice_starts_is_not_a_conflict():
    practice = create_practice(day=Day.MONDAY, start_time=time(9), end_time=time(11))
    class_block = create_class_block(start=8, end=9)
    assert has_conflict([class_block], practice, WEEK_START) is False

def test_same_time_different_day_is_not_a_conflict():
    practice = create_practice(day=Day.TUESDAY, start_time=time(8), end_time=time(9))
    class_block = create_class_block(start=8, end=9)
    assert has_conflict([class_block], practice, WEEK_START) is False

def test_no_classes_is_not_a_conflict():
    practice = create_practice(day=Day.MONDAY)
    assert has_conflict([], practice, WEEK_START) is False

def test_no_conflicting_swimmers():
    schedule  = create_schedule()
    practice = create_practice()

    issue_swimmers = conflicting_swimmers(practice=practice,
                                          week_start=WEEK_START,
                                          schedules=schedule )

    assert issue_swimmers == set()

def test_a_single_conflicting_swimmer():
    schedule  = create_schedule(swimmers_ids=[1,2],
                               class_blocks=[[create_class_block(start=8,end=9),
                                              create_class_block(start=9,end=11)],
                                             []])
    practice = create_practice(start_time=time(9), end_time=time(10), day=Day.MONDAY)

    issue_swimmers = conflicting_swimmers(practice=practice,
                                          week_start=WEEK_START,
                                          schedules=schedule )

    assert issue_swimmers == {1}

def test_a_single_conflicting_swimmer_second_no_conflict_but_has_classes():
    schedule  = create_schedule(swimmers_ids=[1,2],
                               class_blocks=[[create_class_block(start=8,end=9),
                                              create_class_block(start=9,end=11)],
                                             [create_class_block(start=16,end=18)]])
    practice = create_practice(start_time=time(9), end_time=time(10), day=Day.MONDAY)

    issue_swimmers = conflicting_swimmers(practice=practice,
                                          week_start=WEEK_START,
                                          schedules=schedule )

    assert issue_swimmers == {1}

def test_weekstart_not_monday():
    practice = create_practice()
    saturday = date(year=2026,month=11,day=7)

    with pytest.raises(ValueError, match="monday"):
        start, end = practice_block(practice, saturday)


# ---------- get_swimmers_status_for_practice ----------
# These use the real fixture calendars. sample_schedule.ics has MATH 210 on
# Tuesdays 1:00-2:15 pm (through Dec 11, 2026); floating_times.ics has one
# class, BIO 150, on Tue 11/10 10:00-11:00 am. Each test builds its own list
# of swimmers and passes it in, so nothing touches the app's storage.

FIXTURES = Path(__file__).parent / "fixtures"
SAMPLE_ICS = (FIXTURES / "sample_schedule.ics").read_bytes()
FLOATING_ICS = (FIXTURES / "floating_times.ics").read_bytes()
WEEK_OF_NOV_9 = date(2026, 11, 9)

def make_swimmer(swimmer_id, ics_data=None):
    return Swimmer(first_name="Test",
                   last_name=f"Swimmer{swimmer_id}",
                   swimmer_id=swimmer_id,
                   weights_group=WeightsGroup.FOUR_DAY,
                   ics_data=ics_data)

def test_status_one_swimmer_in_each_state():
    swimmers = [make_swimmer(1, SAMPLE_ICS),     # MATH 210 overlaps the 1:30 practice
                make_swimmer(2),                 # no calendar uploaded
                make_swimmer(3, FLOATING_ICS)]   # only has a morning class
    practice = create_practice(start_time=time(13, 30), end_time=time(15))

    result = get_swimmers_status_for_practice(practice, WEEK_OF_NOV_9, swimmers)

    assert result.available == [3]
    assert result.conflict == [1]
    assert result.unknown == [2]

def test_status_no_calendar_is_unknown_not_available():
    # A 5 am practice conflicts with nobody, but a swimmer with no calendar
    # still isn't "available" - we just don't know.
    practice = create_practice(start_time=time(5), end_time=time(6))

    result = get_swimmers_status_for_practice(practice, WEEK_OF_NOV_9, [make_swimmer(1)])

    assert result.unknown == [1]
    assert result.available == []

def test_status_with_no_swimmers_is_all_empty():
    result = get_swimmers_status_for_practice(create_practice(), WEEK_OF_NOV_9, [])

    assert result.available == []
    assert result.conflict == []
    assert result.unknown == []

def test_status_midweek_date_matches_monday():
    swimmers = [make_swimmer(1, SAMPLE_ICS), make_swimmer(2, FLOATING_ICS)]
    practice = create_practice(start_time=time(13, 30), end_time=time(15))

    from_monday = get_swimmers_status_for_practice(practice, WEEK_OF_NOV_9, swimmers)
    from_wednesday = get_swimmers_status_for_practice(practice, date(2026, 11, 11), swimmers)

    assert from_wednesday == from_monday

def test_status_week_with_no_classes_makes_everyone_available():
    # The sample classes end Dec 11, 2026, so the week of Dec 14 is empty.
    swimmers = [make_swimmer(1, SAMPLE_ICS), make_swimmer(2, FLOATING_ICS)]
    practice = create_practice(start_time=time(13, 30), end_time=time(15))

    result = get_swimmers_status_for_practice(practice, date(2026, 12, 14), swimmers)

    assert result.available == [1, 2]
    assert result.conflict == []

def test_status_practice_starting_when_class_ends_is_available():
    # MATH 210 ends at 2:15; a practice starting at 2:15 is not a conflict.
    practice = create_practice(start_time=time(14, 15), end_time=time(16))

    result = get_swimmers_status_for_practice(practice, WEEK_OF_NOV_9,
                                              [make_swimmer(1, SAMPLE_ICS)])

    assert result.available == [1]

def test_status_lists_are_sorted_by_id():
    # Passed in out of order; sets have no order, so the function must sort.
    swimmers = ([make_swimmer(i, SAMPLE_ICS) for i in (3, 1, 2)]
                + [make_swimmer(i) for i in (6, 4, 5)])
    practice = create_practice(start_time=time(13, 30), end_time=time(15))

    result = get_swimmers_status_for_practice(practice, WEEK_OF_NOV_9, swimmers)

    assert result.conflict == [1, 2, 3]
    assert result.unknown == [4, 5, 6]

def test_status_only_uses_the_swimmers_passed_in():
    # e.g. the coach filtered the panel to one tag group - only those count.
    distance = make_swimmer(1, SAMPLE_ICS)
    distance.tags = {"Distance"}
    sprint = make_swimmer(2, SAMPLE_ICS)
    everyone = [distance, sprint]
    practice = create_practice(start_time=time(13, 30), end_time=time(15))

    only_distance = [s for s in everyone if "Distance" in s.tags]
    result = get_swimmers_status_for_practice(practice, WEEK_OF_NOV_9, only_distance)

    assert result.conflict == [1]
    assert 2 not in result.available + result.conflict + result.unknown

def test_status_accepts_dict_values():
    # The route passes swimmers.values(), not a list. Any iterable should work.
    by_id = {1: make_swimmer(1, SAMPLE_ICS), 2: make_swimmer(2)}
    practice = create_practice(start_time=time(13, 30), end_time=time(15))

    result = get_swimmers_status_for_practice(practice, WEEK_OF_NOV_9, by_id.values())

    assert result.conflict == [1]
    assert result.unknown == [2]
