from datetime import date, datetime, timedelta

from app.models import Practice
from app.intervals import overlapChecker
from app.ics_parser import LOCAL_TZ

def practice_block(practice: Practice, week_start: date) -> tuple[datetime, datetime]:
    """Turn 'Tuesday 6:00-8:00' into real datetimes for the given week."""

    if week_start.weekday() != 0:
        raise ValueError("start of week must be a monday")

    start = practice.start_time
    end = practice.end_time

    day = week_start + timedelta(days=practice.day.value - 1)

    practice_datetime_start = datetime.combine(day, practice.start_time, tzinfo=LOCAL_TZ)
    practice_datetime_end = datetime.combine(day, practice.end_time, tzinfo=LOCAL_TZ)

    return (practice_datetime_start, practice_datetime_end)

def has_conflict(class_blocks, practice: Practice, week_start: date) -> bool:
    """True if any of this swimmer's classes overlap the practice."""
    practice_start_end = practice_block(practice, week_start)

    return overlapChecker(class_blocks, practice_start_end)

def conflicting_swimmers(practice: Practice, week_start: date,
                         schedules: dict[int, list[tuple[datetime, datetime]]]) -> set[int]:
    """Return the ids of swimmers who can't make this practice."""
    result: set[int] = set()

    for swimmer_id, class_blocks in schedules.items():
        if has_conflict(class_blocks=class_blocks, practice=practice, week_start=week_start):
            result.add(swimmer_id)

    return result
        
