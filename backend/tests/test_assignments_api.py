"""Tests for assigning swimmers to practices.

PUT    /practices/{practice_id}/swimmers/{swimmer_id}  assign (204, no body)
DELETE /practices/{practice_id}/swimmers/{swimmer_id}  unassign (204, no body)
GET    /practices/{practice_id}/swimmers               list a practice's swimmers
GET    /swimmers/{swimmer_id}/practices                list a swimmer's practices

Deleting a swimmer or a practice also removes its assignments.

Assignments are the same every week, and the coach can assign anyone, even a
swimmer whose classes conflict (the gray-out in the UI is only a warning).
"""

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.storage import assignments

client = TestClient(app)

FIXTURES = Path(__file__).parent / "fixtures"
SAMPLE_ICS = (FIXTURES / "sample_schedule.ics").read_bytes()

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

def assign(practice_id: int, swimmer_id: int):
    return client.put(f"/practices/{practice_id}/swimmers/{swimmer_id}")

def unassign(practice_id: int, swimmer_id: int):
    return client.delete(f"/practices/{practice_id}/swimmers/{swimmer_id}")

def swimmer_practice_ids(swimmer_id: int) -> list[int]:
    """GET a swimmer's practices and return just their ids, in the order returned."""
    response = client.get(f"/swimmers/{swimmer_id}/practices")
    assert response.status_code == 200
    return [practice["practice_id"] for practice in response.json()]

def practice_swimmer_ids(practice_id: int) -> list[int]:
    """GET a practice's swimmers and return just their ids, in the order returned."""
    response = client.get(f"/practices/{practice_id}/swimmers")
    assert response.status_code == 200
    return [swimmer["swimmer_id"] for swimmer in response.json()]

# ---------- PUT (assign) ----------

def test_assign_returns_204_with_no_body():
    practice_id = create_practice()["practice_id"]
    swimmer_id = create_swimmer()["swimmer_id"]

    response = assign(practice_id, swimmer_id)

    assert response.status_code == 204
    assert response.content == b""

def test_assign_then_list_shows_the_swimmer():
    practice_id = create_practice()["practice_id"]
    swimmer_id = create_swimmer()["swimmer_id"]

    assign(practice_id, swimmer_id)

    assert practice_swimmer_ids(practice_id) == [swimmer_id]

def test_assigning_twice_lists_the_swimmer_once():
    # PUT is idempotent: doing it again is not an error and changes nothing.
    practice_id = create_practice()["practice_id"]
    swimmer_id = create_swimmer()["swimmer_id"]

    first = assign(practice_id, swimmer_id)
    second = assign(practice_id, swimmer_id)

    assert first.status_code == 204
    assert second.status_code == 204
    assert practice_swimmer_ids(practice_id) == [swimmer_id]
    assert len(assignments) == 1

def test_assign_to_missing_practice_returns_404_and_stores_nothing():
    swimmer_id = create_swimmer()["swimmer_id"]

    response = assign(999, swimmer_id)

    assert response.status_code == 404
    assert response.json()["detail"] == "Practice not found"
    assert len(assignments) == 0

def test_assign_missing_swimmer_returns_404_and_stores_nothing():
    practice_id = create_practice()["practice_id"]

    response = assign(practice_id, 999)

    assert response.status_code == 404
    assert response.json()["detail"] == "Swimmer not found"
    assert len(assignments) == 0

def test_assign_swimmer_with_a_class_conflict_is_allowed():
    # The coach decides. A conflict grays the swimmer out but doesn't block them.
    practice_id = create_practice()["practice_id"]
    swimmer_id = create_swimmer()["swimmer_id"]
    client.put(f"/swimmers/{swimmer_id}/schedule",
               files={"file": ("schedule.ics", SAMPLE_ICS, "text/calendar")})
    conflicts = client.get(f"/practices/{practice_id}/conflicts",
                           params={"week": "2026-11-09"}).json()
    assert swimmer_id in conflicts["conflict"]   # make sure it really is a conflict

    response = assign(practice_id, swimmer_id)

    assert response.status_code == 204
    assert practice_swimmer_ids(practice_id) == [swimmer_id]

# ---------- DELETE (unassign) ----------

def test_unassign_returns_204_and_removes_the_swimmer():
    practice_id = create_practice()["practice_id"]
    swimmer_id = create_swimmer()["swimmer_id"]
    assign(practice_id, swimmer_id)

    response = unassign(practice_id, swimmer_id)

    assert response.status_code == 204
    assert response.content == b""
    assert practice_swimmer_ids(practice_id) == []

def test_unassign_only_removes_that_swimmer():
    practice_id = create_practice()["practice_id"]
    staying = create_swimmer(first_name="Staying")["swimmer_id"]
    leaving = create_swimmer(first_name="Leaving")["swimmer_id"]
    assign(practice_id, staying)
    assign(practice_id, leaving)

    unassign(practice_id, leaving)

    assert practice_swimmer_ids(practice_id) == [staying]

def test_unassign_only_removes_that_practice():
    # A swimmer in two practices, removed from one, stays in the other.
    morning_id = create_practice(start_time="06:00:00", end_time="08:00:00",
                                 is_morning=True)["practice_id"]
    afternoon_id = create_practice()["practice_id"]
    swimmer_id = create_swimmer()["swimmer_id"]
    assign(morning_id, swimmer_id)
    assign(afternoon_id, swimmer_id)

    unassign(morning_id, swimmer_id)

    assert practice_swimmer_ids(morning_id) == []
    assert practice_swimmer_ids(afternoon_id) == [swimmer_id]

def test_unassign_swimmer_who_is_not_assigned_returns_404():
    # Decided (Nov 26): 404 rather than 204, so frontend mistakes show up.
    practice_id = create_practice()["practice_id"]
    swimmer_id = create_swimmer()["swimmer_id"]

    response = unassign(practice_id, swimmer_id)

    assert response.status_code == 404
    assert response.json()["detail"] == "Swimmer is not assigned to this practice"

def test_unassigning_twice_returns_404_the_second_time():
    practice_id = create_practice()["practice_id"]
    swimmer_id = create_swimmer()["swimmer_id"]
    assign(practice_id, swimmer_id)

    first = unassign(practice_id, swimmer_id)
    second = unassign(practice_id, swimmer_id)

    assert first.status_code == 204
    assert second.status_code == 404

def test_unassign_from_missing_practice_returns_404():
    swimmer_id = create_swimmer()["swimmer_id"]

    response = unassign(999, swimmer_id)

    assert response.status_code == 404
    assert response.json()["detail"] == "Practice not found"

def test_unassign_missing_swimmer_returns_404():
    practice_id = create_practice()["practice_id"]

    response = unassign(practice_id, 999)

    assert response.status_code == 404
    assert response.json()["detail"] == "Swimmer not found"

def test_can_reassign_after_unassigning():
    practice_id = create_practice()["practice_id"]
    swimmer_id = create_swimmer()["swimmer_id"]
    assign(practice_id, swimmer_id)
    unassign(practice_id, swimmer_id)

    response = assign(practice_id, swimmer_id)

    assert response.status_code == 204
    assert practice_swimmer_ids(practice_id) == [swimmer_id]

# ---------- GET (list a practice's swimmers) ----------

def test_list_practice_with_no_swimmers_is_empty():
    practice_id = create_practice()["practice_id"]

    assert practice_swimmer_ids(practice_id) == []

def test_list_missing_practice_returns_404():
    # Not an empty list: "no such practice" and "no swimmers yet" are different.
    response = client.get("/practices/999/swimmers")

    assert response.status_code == 404
    assert response.json()["detail"] == "Practice not found"

def test_list_is_sorted_by_swimmer_id():
    practice_id = create_practice()["practice_id"]
    ids = [create_swimmer(first_name=name)["swimmer_id"] for name in ("A", "B", "C")]

    for swimmer_id in reversed(ids):
        assign(practice_id, swimmer_id)

    assert practice_swimmer_ids(practice_id) == sorted(ids)

def test_list_only_includes_that_practices_swimmers():
    morning_id = create_practice(start_time="06:00:00", end_time="08:00:00",
                                 is_morning=True)["practice_id"]
    afternoon_id = create_practice()["practice_id"]
    both = create_swimmer(first_name="Both")["swimmer_id"]
    morning_only = create_swimmer(first_name="Morning")["swimmer_id"]

    assign(morning_id, both)
    assign(afternoon_id, both)
    assign(morning_id, morning_only)

    assert practice_swimmer_ids(morning_id) == [both, morning_only]
    assert practice_swimmer_ids(afternoon_id) == [both]

def test_list_returns_full_swimmers_without_ics_data():
    practice_id = create_practice()["practice_id"]
    swimmer = create_swimmer()
    client.put(f"/swimmers/{swimmer['swimmer_id']}/schedule",
               files={"file": ("schedule.ics", SAMPLE_ICS, "text/calendar")})

    assign(practice_id, swimmer["swimmer_id"])
    listed = client.get(f"/practices/{practice_id}/swimmers").json()[0]

    assert listed["first_name"] == "Austin"
    assert listed["weights_group"] == "FOUR_DAY"
    assert listed["has_schedule"] is True
    assert "ics_data" not in listed

# ---------- GET (list a swimmer's practices) ----------

def test_swimmer_with_no_practices_is_empty():
    swimmer_id = create_swimmer()["swimmer_id"]

    assert swimmer_practice_ids(swimmer_id) == []

def test_list_swimmer_practices_for_missing_swimmer_returns_404():
    response = client.get("/swimmers/999/practices")

    assert response.status_code == 404
    assert response.json()["detail"] == "Swimmer not found"

def test_swimmer_practices_sorted_and_only_their_own():
    ids = [create_practice(day=day)["practice_id"] for day in (1, 3, 5)]
    swimmer_id = create_swimmer(first_name="In all three")["swimmer_id"]
    other_id = create_swimmer(first_name="Only Monday")["swimmer_id"]

    for practice_id in reversed(ids):
        assign(practice_id, swimmer_id)
    assign(ids[0], other_id)

    assert swimmer_practice_ids(swimmer_id) == sorted(ids)
    assert swimmer_practice_ids(other_id) == [ids[0]]

def test_swimmer_practices_returns_full_practices():
    practice = create_practice()
    swimmer_id = create_swimmer()["swimmer_id"]
    assign(practice["practice_id"], swimmer_id)

    response = client.get(f"/swimmers/{swimmer_id}/practices")

    assert response.status_code == 200
    assert response.json() == [practice]

def test_unassign_removes_practice_from_swimmer_list():
    practice_id = create_practice()["practice_id"]
    swimmer_id = create_swimmer()["swimmer_id"]
    assign(practice_id, swimmer_id)

    unassign(practice_id, swimmer_id)

    assert swimmer_practice_ids(swimmer_id) == []

# ---------- deleting a swimmer or practice cleans up its assignments ----------

def test_deleting_a_practice_removes_its_assignments():
    deleted_id = create_practice()["practice_id"]
    kept_id = create_practice(day=4)["practice_id"]
    swimmer_id = create_swimmer()["swimmer_id"]
    assign(deleted_id, swimmer_id)
    assign(kept_id, swimmer_id)

    assert client.delete(f"/practices/{deleted_id}").status_code == 204

    # Without the cleanup this would crash with a KeyError on the deleted practice.
    assert swimmer_practice_ids(swimmer_id) == [kept_id]
    assert all(a.practice_id != deleted_id for a in assignments)

def test_deleting_a_swimmer_removes_their_assignments():
    practice_id = create_practice()["practice_id"]
    deleted_id = create_swimmer(first_name="Deleted")["swimmer_id"]
    kept_id = create_swimmer(first_name="Kept")["swimmer_id"]
    assign(practice_id, deleted_id)
    assign(practice_id, kept_id)

    assert client.delete(f"/swimmers/{deleted_id}").status_code == 204

    # Without the cleanup this would crash with a KeyError on the deleted swimmer.
    assert practice_swimmer_ids(practice_id) == [kept_id]
    assert all(a.swimmer_id != deleted_id for a in assignments)

def test_deleting_a_practice_with_no_assignments_still_works():
    practice_id = create_practice()["practice_id"]

    assert client.delete(f"/practices/{practice_id}").status_code == 204
