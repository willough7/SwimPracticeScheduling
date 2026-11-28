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

## Features
- **Schedule:** day-of-week tabs with an hourly calendar of that day's
  practices (overlapping practices sit side by side)
- **Swimmer panel:** a resizable bottom panel with name search and filters for
  weights group and coach-created tags (e.g. 100s, 200s, IM, Distance)
- **Assigning:** click a practice to see who can make it (swimmers with a class
  conflict are grayed out, swimmers with no calendar are flagged), then click
  swimmers to assign them
- **Lanes:** double-click a practice to open its 8 pool lanes and drag assigned
  swimmers into them (right-click a swimmer to move them without dragging)
- **Editing:** add and edit swimmers and practices in dialogs, or from
  right-click menus; swimmers upload their own `.ics` calendar from their card
- **Export and print:** download the whole week as an Excel file (a sheet per
  day, lanes as columns), or print one day's practices
- **Admin login:** admins create and edit; everyone else can view and upload
  calendars without an account
- **Planned:** a database, so data survives restarts; per-week overrides for
  meets and holidays

## Tech stack
- **Frontend:** React + TypeScript, built and served in development by Vite
- **Backend:** Python 3.12 + FastAPI, Pydantic for request/response validation
- **Storage:** in memory for now, so restarting the backend clears all data
  (admin accounts are the exception: they're saved in `backend/admins.json`)
- **Database (planned):** PostgreSQL (hosted on Supabase) in production; SQLite
  for automated tests. Data access will go through an ORM so the two can be
  swapped by changing the connection URL.
- **Calendar parsing:** icalendar + recurring-ical-events
- **Excel export:** openpyxl
- **Testing:** pytest, FastAPI TestClient; ESLint and TypeScript checks for the frontend

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
    export.py       # builds the Excel workbook
    auth.py         # login sessions, the session cookie, and require_admin
    admin_accounts.py  # admin usernames and password hashes (admins.json)
    manage_admins.py   # command-line tool to add, remove, and list admins
    main.py         # FastAPI app and routes
  tests/            # pytest suite, one file per module or API resource
    fixtures/       # small made-up .ics calendars (real ones hold student data)
frontend/
  src/
    App.tsx         # the whole page: state, data loading, and event handlers
    api.ts          # one function per backend endpoint; the only file that calls fetch
    types.ts        # TypeScript versions of the backend's schemas
    components/     # one file per piece of the screen (ScheduleView, SwimmerPanel,
                    #   LanesView, the forms and dialogs, ...)
    time.ts, labels.ts, dragDrop.ts   # small shared helpers
    index.css       # theme colors (CSS variables); App.css has the rest of the styles
  scripts/
    seed-test-data.mjs  # loads 75 made-up swimmers and 3 practices a day
  vite.config.ts    # dev server; forwards /api/... to the backend on port 8000
```

## Admin login
Admins log in to create and edit; everyone else uses the app without an
account. Swimmers can open their own card and upload their class calendar
without logging in (a deliberate trade-off: anyone could replace any
swimmer's calendar, which is acceptable for a team-sized app).

| Who | Can |
|---|---|
| Anyone | View everything, export/print, upload a swimmer's `.ics` calendar |
| Logged-in admin | Also create, edit, and delete swimmers and practices, assign swimmers, and arrange lanes |

The backend enforces this: every create/edit/delete/assign/lane route answers
`401 "Admin login required"` without an admin session, whatever the frontend shows.

### Managing admin accounts
Accounts can only be made on the server, never from the website:

```bash
python -m app.manage_admins add <username>      # create, or change the password
python -m app.manage_admins remove <username>
python -m app.manage_admins list
```

Run these from the `backend` folder with the virtual environment active.
`<username>` is a placeholder: type the name itself, without the angle brackets
(`python -m app.manage_admins add austin`). In Git Bash the password shows as
you type it; in PowerShell or Command Prompt it's hidden.

Accounts are saved in `backend/admins.json` (git-ignored). Passwords are stored
only as salted scrypt hashes, and must be at least 10 characters.

### How logins work
- `POST /auth/login` with `{"username", "password"}` sets an `admin_session`
  cookie: `HttpOnly` (page scripts can't read it), `Secure` (HTTPS only;
  browsers allow `localhost` too), and `SameSite=Strict` (never sent with
  requests started by other websites). A login lasts 12 hours.
- `POST /auth/logout` ends it; `GET /auth/me` returns `{"username": ...}`, or `null`.
- Sessions are kept in memory, so restarting the backend logs everyone out.
- Wrong username and wrong password get the same `401 "Wrong username or password"`.
- There is no lockout after wrong passwords. This is a deliberate trade-off
  (a lockout lets anyone who knows an admin's username lock them out); it means
  someone could keep guessing, so admin passwords should be long and not reused
  from other sites.
- When hosted online the site **must** be served over HTTPS, or the `Secure`
  cookie won't be sent and admins can't stay logged in.

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
| PUT | `/swimmers/{swimmer_id}` | Replace a swimmer's details (name, weights group, tags); keeps their id, calendar, and assignments | 200 |
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
| PUT | `/practices/{practice_id}` | Replace every field of a practice; keeps its id and assignments | 200 |
| DELETE | `/practices/{practice_id}` | Delete a practice | 204 |
| GET | `/practices/{practice_id}/conflicts?week=YYYY-MM-DD` | Which swimmers can make this practice in the given week | 200 |

### Assignments
| Method | Path | Does | Success |
|---|---|---|---|
| PUT | `/practices/{practice_id}/swimmers/{swimmer_id}` | Assign a swimmer to a practice | 204 |
| DELETE | `/practices/{practice_id}/swimmers/{swimmer_id}` | Remove a swimmer from a practice | 204 |
| GET | `/practices/{practice_id}/swimmers` | Swimmers assigned to a practice, sorted by id | 200 |
| GET | `/swimmers/{swimmer_id}/practices` | Practices a swimmer is assigned to, sorted by id | 200 |

- Assignments repeat every week; there are no per-week assignments yet.
- An admin can assign any swimmer, including one whose classes conflict with
  the practice. The conflict gray-out is a warning, not a rule.
- Assigning a swimmer who is already assigned succeeds and changes nothing.
  Removing a swimmer who isn't assigned returns 404
  (`"Swimmer is not assigned to this practice"`), so frontend mistakes show up.
- Deleting a swimmer or a practice also removes its assignments.

### Lanes
| Method | Path | Does | Success |
|---|---|---|---|
| PUT | `/practices/{practice_id}/swimmers/{swimmer_id}/lane` | Put an assigned swimmer in lane 1-8 (`{"lane": 3}`), or take them out of their lane (`{"lane": null}`) | 204 |
| GET | `/practices/{practice_id}/lanes` | Placed swimmers as `{"swimmer_id", "lane"}`, sorted by lane then swimmer id | 200 |

- Only assigned swimmers can be placed (404 `"Swimmer is not assigned to this practice"` otherwise); lanes outside 1-8 are 422.
- Taking a swimmer out of their lane keeps them assigned. Unassigning them, or deleting the swimmer or practice, removes their lane.
- Lanes repeat every week, like assignments.

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

### Export
| Method | Path | Does | Success |
|---|---|---|---|
| GET | `/export/week.xlsx?day=1`-`7` | The whole week as an Excel file: a sheet per day, each practice with Lane 1-8 and "Not in a lane" as columns. `day` picks the sheet it opens on (default Monday). | 200 |

The response is sent as a download (`Content-Disposition: attachment`) named
`practice-schedule.xlsx`. Sheets print landscape, one page wide. Printing a
single day is done by the frontend's Print day button instead.

### Status codes
| Code | Meaning | Where it comes from |
|---|---|---|
| 200 OK | Successful read | FastAPI default when a route returns normally |
| 201 Created | New resource created | Set with `status_code=201` on the route |
| 204 No Content | Success, no response body (deletes) | Set with `status_code=204` on the route |
| 400 Bad Request | The uploaded file isn't a valid `.ics` calendar | Raised in our code with `HTTPException` (`"File is not a valid .ics calendar"`) |
| 401 Unauthorized | Not logged in as an admin, or wrong login details | Raised by `require_admin` (`"Admin login required"`) and by `/auth/login` |
| 404 Not Found | The requested item doesn't exist | Raised in our code with `HTTPException` (`"Swimmer not found"`, `"Practice not found"`, `"Swimmer is not assigned to this practice"`). FastAPI also returns a plain `"Not Found"` for URLs with no matching route. |
| 422 Unprocessable Entity | Request body, path, or query failed validation (e.g. a missing file or `?week=banana`) | Raised automatically by FastAPI/Pydantic; the route never runs |
| 500 Internal Server Error | A bug: an unhandled exception in our code | Raised automatically; details appear in the server terminal, not the response |

## Running locally
You need Python 3.12 and Node.js (LTS). Run the backend and the frontend in
two separate terminals.

**Backend**, from the `backend` folder:

```bash
python -m venv .venv
source .venv/Scripts/activate    # Windows (Git Bash)
source .venv/bin/activate        # macOS / Linux
pip install -r requirements.txt

python -m app.manage_admins add <username>   # first time only: create an admin account
fastapi dev app/main.py          # API at http://127.0.0.1:8000, docs at /docs
pytest                           # run the test suite
```

**Frontend**, from the `frontend` folder:

```bash
npm install                      # first time, and after dependencies change
npm run dev                      # the app at http://localhost:5173
npm run lint                     # check the code with ESLint
npm run seed                     # load test data (asks for your admin login)
npm run seed -- --reset          # clear everything first, then load test data
```

Open the app at `http://localhost:5173`, not port 8000: Vite forwards every
request starting with `/api` to the backend, so the browser only ever talks
to one address.

Because data is kept in memory, **restarting the backend clears everything**,
and `fastapi dev` restarts itself whenever a backend file changes. Run
`npm run seed` again afterwards to get test data back.

## Status
In active development. Done: .ics parsing and conflict detection; the API for
swimmers, practices, calendar uploads, assignments, lanes, Excel export, and
admin login, all covered by tests; and the React frontend described under
Features. Next: the database, so data survives restarts.
