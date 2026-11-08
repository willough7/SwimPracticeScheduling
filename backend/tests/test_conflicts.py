from datetime import date, time, datetime
import pytest

from app.models import Practice, Day
from app.conflicts import practice_block, has_conflict, conflicting_swimmers
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

    