"""Tests for GET /practices/{practice_id}/conflicts?week=YYYY-MM-DD.

The grouping logic itself is tested in test_conflicts.py. These tests check
the HTTP side: the 404 and 422 errors, the response shape, and that the
pieces work together (create swimmers, upload calendars, then ask).
"""

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

FIXTURES = Path(__file__).parent / "fixtures"
SAMPLE_ICS = (FIXTURES / "sample_schedule.ics").read_bytes()
FLOATING_ICS = (FIXTURES / "floating_times.ics").read_bytes()

VALID_SWIMMER = {
    "first_name": "Austin",
    "last_name": "Willoughby",
    "weights_group": "FOUR_DAY",
    "tags": ["100s", "Sprint"],
}

# Tuesday 1:30-3:00 pm, which overlaps MATH 210 (1:00-2:15) in sample_schedule.ics.
TUESDAY_PRACTICE = {
    "day": 2,
    "start_time": "13:30:00",
    "end_time": "15:00:00",
    "practice_title": "Afternoon swim",
    "is_morning": False,
}

def create_swimmer(**overrides) -> dict:
    """POST a valid swimmer, with any fields overridden, and return the response body."""
    response = client.post("/swimmers", json={**VALID_SWIMMER, **overrides})
    assert response.status_code == 201
    return response.json()

def create_practice(**overrides) -> dict:
    """POST a valid practice, with any fields overridden, and return the response body."""
    response = client.post("/practices", json={**TUESDAY_PRACTICE, **overrides})
    assert response.status_code == 201
    return response.json()

def upload_schedule(swimmer_id: int, data: bytes):
    response = client.put(
        f"/swimmers/{swimmer_id}/schedule",
        files={"file": ("schedule.ics", data, "text/calendar")},
    )
    assert response.status_code == 200

def get_conflicts(practice_id: int, week: str):
    return client.get(f"/practices/{practice_id}/conflicts", params={"week": week})

def test_conflicts_groups_swimmers_by_status():
    conflict_id = create_swimmer(first_name="Conflict")["swimmer_id"]
    unknown_id = create_swimmer(first_name="Unknown")["swimmer_id"]
    available_id = create_swimmer(first_name="Available")["swimmer_id"]
    upload_schedule(conflict_id, SAMPLE_ICS)
    upload_schedule(available_id, FLOATING_ICS)
    practice_id = create_practice()["practice_id"]

    response = get_conflicts(practice_id, "2026-11-09")

    assert response.status_code == 200
    assert response.json() == {
        "practice_id": practice_id,
        "week_start": "2026-11-09",
        "available": [available_id],
        "conflict": [conflict_id],
        "unknown": [unknown_id],
    }

def test_conflicts_midweek_date_reports_monday_as_week_start():
    practice_id = create_practice()["practice_id"]

    response = get_conflicts(practice_id, "2026-11-11")   # a Wednesday

    assert response.status_code == 200
    assert response.json()["week_start"] == "2026-11-09"

def test_conflicts_with_no_swimmers_returns_empty_lists():
    practice_id = create_practice()["practice_id"]

    response = get_conflicts(practice_id, "2026-11-09")

    assert response.status_code == 200
    body = response.json()
    assert body["available"] == []
    assert body["conflict"] == []
    assert body["unknown"] == []

def test_conflicts_for_missing_practice_returns_404():
    response = get_conflicts(999, "2026-11-09")

    assert response.status_code == 404
    assert response.json()["detail"] == "Practice not found"

def test_conflicts_without_week_returns_422():
    practice_id = create_practice()["practice_id"]

    response = client.get(f"/practices/{practice_id}/conflicts")

    assert response.status_code == 422

def test_conflicts_with_invalid_week_returns_422():
    practice_id = create_practice()["practice_id"]

    response = get_conflicts(practice_id, "banana")

    assert response.status_code == 422

def test_conflicts_does_not_change_anything():
    # GET should only read. Asking twice gives the same answer.
    swimmer_id = create_swimmer()["swimmer_id"]
    upload_schedule(swimmer_id, SAMPLE_ICS)
    practice_id = create_practice()["practice_id"]

    first = get_conflicts(practice_id, "2026-11-09").json()
    second = get_conflicts(practice_id, "2026-11-09").json()

    assert first == second
    assert client.get(f"/swimmers/{swimmer_id}").json()["has_schedule"] is True
