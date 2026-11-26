"""Tests for PUT /swimmers/{swimmer_id}/schedule (uploading a swimmer's .ics file).

Files are sent as multipart form data with files= instead of json=. The key
"file" must match the route's parameter name.
"""

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.storage import swimmers

client = TestClient(app)

FIXTURES = Path(__file__).parent / "fixtures"
SAMPLE_ICS = (FIXTURES / "sample_schedule.ics").read_bytes()
FLOATING_ICS = (FIXTURES / "floating_times.ics").read_bytes()
EMPTY_CALENDAR = b"BEGIN:VCALENDAR\r\nVERSION:2.0\r\nPRODID:-//test//EN\r\nEND:VCALENDAR\r\n"

VALID_SWIMMER = {
    "first_name": "Austin",
    "last_name": "Willoughby",
    "weights_group": "FOUR_DAY",
    "tags": ["100s", "Sprint"],
}

def create_swimmer(**overrides) -> dict:
    """POST a valid swimmer, with any fields overridden, and return the response body."""
    response = client.post("/swimmers", json={**VALID_SWIMMER, **overrides})
    assert response.status_code == 201
    return response.json()

def upload_schedule(swimmer_id: int, data: bytes, filename: str = "schedule.ics"):
    """PUT the given bytes as a swimmer's schedule file and return the response."""
    return client.put(
        f"/swimmers/{swimmer_id}/schedule",
        files={"file": (filename, data, "text/calendar")},
    )

def test_upload_valid_schedule_returns_200_and_has_schedule():
    swimmer_id = create_swimmer()["swimmer_id"]

    response = upload_schedule(swimmer_id, SAMPLE_ICS)

    assert response.status_code == 200
    assert response.json()["has_schedule"] is True

def test_upload_stores_the_raw_bytes():
    # has_schedule can't tell bytes from a parsed Calendar, so check storage directly.
    swimmer_id = create_swimmer()["swimmer_id"]

    upload_schedule(swimmer_id, SAMPLE_ICS)

    assert swimmers[swimmer_id].ics_data == SAMPLE_ICS

def test_get_swimmer_after_upload_shows_has_schedule():
    swimmer_id = create_swimmer()["swimmer_id"]
    upload_schedule(swimmer_id, SAMPLE_ICS)

    response = client.get(f"/swimmers/{swimmer_id}")

    assert response.status_code == 200
    assert response.json()["has_schedule"] is True

def test_upload_invalid_file_returns_400_and_stores_nothing():
    swimmer_id = create_swimmer()["swimmer_id"]

    response = upload_schedule(swimmer_id, b"not a calendar", filename="notes.ics")

    assert response.status_code == 400
    assert response.json()["detail"] == "File is not a valid .ics calendar"
    assert swimmers[swimmer_id].ics_data is None
    assert client.get(f"/swimmers/{swimmer_id}").json()["has_schedule"] is False

def test_upload_empty_file_returns_400():
    swimmer_id = create_swimmer()["swimmer_id"]

    response = upload_schedule(swimmer_id, b"")

    assert response.status_code == 400
    assert swimmers[swimmer_id].ics_data is None

def test_upload_to_missing_swimmer_returns_404():
    response = upload_schedule(999, SAMPLE_ICS)

    assert response.status_code == 404
    assert response.json()["detail"] == "Swimmer not found"

def test_upload_with_no_file_returns_422():
    swimmer_id = create_swimmer()["swimmer_id"]

    response = client.put(f"/swimmers/{swimmer_id}/schedule")

    assert response.status_code == 422

def test_reupload_replaces_the_old_schedule():
    swimmer_id = create_swimmer()["swimmer_id"]
    upload_schedule(swimmer_id, SAMPLE_ICS)

    response = upload_schedule(swimmer_id, FLOATING_ICS)

    assert response.status_code == 200
    assert swimmers[swimmer_id].ics_data == FLOATING_ICS

def test_invalid_reupload_keeps_the_old_schedule():
    # A bad second upload should be rejected without wiping the good one.
    swimmer_id = create_swimmer()["swimmer_id"]
    upload_schedule(swimmer_id, SAMPLE_ICS)

    response = upload_schedule(swimmer_id, b"not a calendar")

    assert response.status_code == 400
    assert swimmers[swimmer_id].ics_data == SAMPLE_ICS

def test_upload_calendar_with_no_events_is_accepted():
    # Decided (Nov 26): empty calendars are accepted for now. A frontend note
    # for "uploaded a calendar with no classes" is a later update.
    swimmer_id = create_swimmer()["swimmer_id"]

    response = upload_schedule(swimmer_id, EMPTY_CALENDAR)

    assert response.status_code == 200
    assert response.json()["has_schedule"] is True
    assert swimmers[swimmer_id].ics_data == EMPTY_CALENDAR

def test_upload_only_changes_that_swimmer():
    first_id = create_swimmer()["swimmer_id"]
    second_id = create_swimmer(first_name="Sam")["swimmer_id"]

    upload_schedule(first_id, SAMPLE_ICS)

    assert swimmers[first_id].ics_data == SAMPLE_ICS
    assert swimmers[second_id].ics_data is None
