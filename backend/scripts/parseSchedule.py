"""Print one week of class times from a school .ics calendar file.

Usage: python scripts/parse_schedule.py <calendar.ics> <any date in the week>
Example: python scripts/parse_schedule.py my_schedule.ics 2026-10-26
"""

import sys
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import icalendar
import recurring_ical_events

LOCAL_TZ = ZoneInfo("America/Indiana/Indianapolis")


def load_calendar(path):
    """Read an .ics file from disk and parse it into a Calendar object."""
    with open(path, "rb") as f:
        return icalendar.Calendar.from_ical(f.read())


def monday_of(day):
    """Return the Monday of the week containing the given date."""
    #timedelta returns the number of days since monday, so day - time since monday will give us the days corresponding monday
    #timedelta handels boundries automaticaly (months, years, leapyears)
    return day - timedelta(days=day.weekday())


def busy_blocks_for_week(calendar, week_start):
    """Return a sorted list of (start, end, name) for every timed event that week."""
    week_end = week_start + timedelta(days=7)
    events = recurring_ical_events.of(calendar).between(week_start, week_end)

    blocks = []
    for event in events:
        start = event["DTSTART"].dt

        # All-day events (holidays, "first day of classes") are dates, not datetimes.
        # They aren't classes, so skip them.
        if not isinstance(start, datetime):
            continue

        # Events specify their length with either DTEND or DURATION.
        if event.get("DTEND"):
            end = event["DTEND"].dt
        else:
            end = start + event["DURATION"].dt

        # Times may be stored in UTC; convert to local time so they read correctly.
        if start.tzinfo is not None:
            start = start.astimezone(LOCAL_TZ)
            end = end.astimezone(LOCAL_TZ)

        name = str(event.get("SUMMARY", "Untitled"))
        blocks.append((start, end, name))

    blocks.sort()
    return blocks


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)

    calendar = load_calendar(sys.argv[1])
    week_start = monday_of(date.fromisoformat(sys.argv[2]))

    print(f"Week of {week_start:%A, %B %d, %Y}\n")
    for start, end, name in busy_blocks_for_week(calendar, week_start):
        print(f"{start:%a}  {start:%I:%M %p} - {end:%I:%M %p}   {name}")


if __name__ == "__main__":
    main()