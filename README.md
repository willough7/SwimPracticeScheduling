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
    models.py       # core dataclasses: Swimmer, Practice, Assignment, SwimmerStatuses
    ics_parser.py   # turns .ics data (uploaded bytes or a file) into busy time blocks
    intervals.py    # merging time blocks and detecting overlaps
    conflicts.py    # sorts swimmers into available / conflict / unknown for a practice
    schemas.py      # API request/response shapes (Pydantic)
    storage.py      # data storage (in-memory for now, database later)
    main.py         # FastAPI app and routes
  tests/            # pytest suite, one file per module or API resource
    fixtures/       # small made-up .ics calendars (real ones hold student data)
```

## API
Interactive docs are generated automatically at `/docs` while the server is
running. Endpoints follow REST conventions: plural nouns name collections,
an id selects one item, and the HTTP method is the action.

### Swimmers
| Method | Path | Does | Success |
|---|---|---|---|
| POST | `/swimmers` | Create a swimmer | 201 |
| GET | `/swimmers` | List all swimmers | 200 |
| GET | `/swimmers/{swimmer_id}` | Get one swimmer | 200 |
| DELETE | `/swimmers/{swimmer_id}` | Delete a swimmer | 204 |
| PUT | `/swimmers/{swimmer_id}/schedule` | Upload the swimmer's `.ics` class calendar (multipart form field `file`); replaces any earlier upload | 200 |

Swimmer responses include `has_schedule`, which is `true` once a valid
calendar has been uploaded. Uploads are validated by actually parsing them
(not by file name or type), and the raw file bytes are stored, so a bad file
is rejected with 400 and never replaces a good one.

### Practices
| Method | Path | Does | Success |
|---|---|---|---|
| POST | `/practices` | Create a practice | 201 |
| GET | `/practices` | List practices, optionally filtered with `?day=1`-`7` (Monday-Sunday) | 200 |
| GET | `/practices/{practice_id}` | Get one practice | 200 |
| DELETE | `/practices/{practice_id}` | Delete a practice | 204 |
| GET | `/practices/{practice_id}/conflicts?week=YYYY-MM-DD` | Which swimmers can make this practice in the given week | 200 |

### Conflicts
Practices repeat weekly ("Tuesday 1:30-3:00"), but class calendars have real
dates, so the conflicts endpoint needs a `week`. Any date in the week works;
it is rounded back to that week's Monday. Every swimmer lands in exactly one
group:

- **available**: has a calendar and no class overlaps the practice
- **conflict**: has a calendar and at least one class overlaps
- **unknown**: hasn't uploaded a calendar, so we can't tell (never treated as free)

A class that ends exactly when practice starts is not a conflict.

```json
GET /practices/3/conflicts?week=2026-11-11

{
  "practice_id": 3,
  "week_start": "2026-11-09",
  "available": [1, 4],
  "conflict": [2],
  "unknown": [3]
}
```

### Status codes
| Code | Meaning | Where it comes from |
|---|---|---|
| 200 OK | Successful read | FastAPI default when a route returns normally |
| 201 Created | New resource created | Set with `status_code=201` on the route |
| 204 No Content | Success, no response body (deletes) | Set with `status_code=204` on the route |
| 400 Bad Request | The uploaded file isn't a valid `.ics` calendar | Raised in our code with `HTTPException` (`"File is not a valid .ics calendar"`) |
| 404 Not Found | The requested item doesn't exist | Raised in our code with `HTTPException` (`"Swimmer not found"`, `"Practice not found"`). FastAPI also returns a plain `"Not Found"` for URLs with no matching route. |
| 422 Unprocessable Entity | Request body, path, or query failed validation (e.g. a missing file or `?week=banana`) | Raised automatically by FastAPI/Pydantic; the route never runs |
| 500 Internal Server Error | A bug: an unhandled exception in our code | Raised automatically; details appear in the server terminal, not the response |

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
detection, data models, and the API for swimmers, practices, calendar uploads,
and per-practice conflict statuses (stored in memory for now), all covered by
tests. Next: assignment endpoints, the React frontend, then the database.
