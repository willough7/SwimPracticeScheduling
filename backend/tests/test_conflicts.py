from datetime import date, time, datetime

from app.models import Practice, Day
from app.conflicts import practice_block
from app.ics_parser import LOCAL_TZ

def test_tuesday_practice_is_on_tuesday():
    practice = Practice(practice_id=1,
                        practice_title="Swim",
                        day=Day.TUESDAY,
                        start_time=time(13),
                        end_time=time(15),
                        is_morning=False)

    week_start = date(year=2026,
                      month=11,
                      day=2)
    
    start, end = practice_block(practice, week_start)

    assert start == datetime(2026, 11, 3, 13, 0, tzinfo=LOCAL_TZ)
    assert end == datetime(2026, 11, 3, 15, 0, tzinfo=LOCAL_TZ)

def test_sunday_practice_is_on_sunday():
    practice = Practice(practice_id=1,
                        practice_title="Swim",
                        day=Day.SUNDAY,
                        start_time=time(13),
                        end_time=time(15),
                        is_morning=False)

    week_start = date(year=2026,
                      month=11,
                      day=2)
    
    start, end = practice_block(practice, week_start)

    assert start == datetime(2026, 11, 8, 13, 0, tzinfo=LOCAL_TZ)
    assert end == datetime(2026, 11, 8, 15, 0, tzinfo=LOCAL_TZ)