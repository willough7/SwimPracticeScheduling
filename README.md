# Swim Practice Scheduler

Helps a swim coach place swimmers into practice times that fit around their
class schedules.

Swimmers provide the .ics calendar file their school generates. The coach
defines the team's practice week, then assigns swimmers to practices by hand.
When the coach selects a practice, the app grays out every swimmer whose
classes conflict with it, and flags swimmers who haven't uploaded a calendar
yet, so the coach can see at a glance who is actually available.

Assignment is deliberately manual: real teams have too many special cases
(meets, injuries, lifting groups, one-off requests) for an algorithm to place
swimmers well. The app's job is to make the coach's decisions fast and
conflict-free, not to make them for the coach.

## Planned features
- Swimmer roster with coach-created tags (e.g. 100s, 200s, IM, Distance) for
  searching and filtering
- Practice week editor
- Schedule view by day of the week, with a resizable swimmer panel
- Conflict gray-out driven by each swimmer's class calendar
- Excel export of the final schedule
- Later: per-week overrides for meets and holidays

## Tech stack
- **Frontend:** React + TypeScript (not started)
- **Backend:** Python 3.12 + FastAPI, Pydantic for request/response validation
- **Database:** PostgreSQL (hosted on Supabase) in production; SQLite for
  automated tests. Data access will go through an ORM so the two can be
  swapped by changing the connection URL.
- **Calendar parsing:** icalendar + recurring-ical-events
- **Testing:** pytest, FastAPI TestClient

## Project structure
```
backend/
  app/
    models.py       # core dataclasses: Swimmer, Practice, Assignment
    ics_parser.py   # turns a school .ics file into busy time blocks
    intervals.py    # merging time blocks and detecting overlaps
    conflicts.py    # which swimmers can't make a given practice
    schemas.py      # API request/response shapes (Pydantic)
    storage.py      # data storage (in-memory for now, database later)
    main.py         # FastAPI app and routes
  tests/            # pytest suite
```

## Running locally
From the `backend` folder:

```bash
python -m venv .venv
source .venv/Scripts/activate    # Windows (Git Bash)
source .venv/bin/activate        # macOS / Linux
pip install -r requirements.txt

fastapi dev app/main.py          # API at http://127.0.0.1:8000, docs at /docs
pytest                           # run the test suite
```

## Status
In active development. Done: .ics parsing, time-block merging and overlap
detection, conflict detection per practice, data models, and the first API
endpoints (swimmer create/list/get/delete, stored in memory). Next: API tests,
practice and conflict endpoints, .ics upload, assignments, then the database.
