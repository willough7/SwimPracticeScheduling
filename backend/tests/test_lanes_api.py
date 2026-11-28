"""Tests for lanes: PUT /practices/{practice_id}/swimmers/{swimmer_id}/lane
and GET /practices/{practice_id}/lanes.

A lane is a number from 1 to 8 for a swimmer who is assigned to the practice.
Sending {"lane": null} takes them out of their lane but leaves them assigned.
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

VALID_SWIMMER = {
    "first_name": "Austin",
    "last_name": "Willoughby",
    "weights_group": "FOUR_DAY",
    "tags": ["100s"],
}

VALID_PRACTICE = {
    "day": 2,
    "start_time": "06:00:00",
    "end_time": "07:30:00",
    "practice_title": "Morning Swim",
}

def create_swimmer(**overrides) -> int:
    response = client.post("/swimmers", json={**VALID_SWIMMER, **overrides})
    assert response.status_code == 201
    return response.json()["swimmer_id"]

def create_practice(**overrides) -> int:
    response = client.post("/practices", json={**VALID_PRACTICE, **overrides})
    assert response.status_code == 201
    return response.json()["practice_id"]

def assign(practice_id: int, swimmer_id: int):
    response = client.put(f"/practices/{practice_id}/swimmers/{swimmer_id}")
    assert response.status_code == 204

def set_lane(practice_id: int, swimmer_id: int, lane):
    return client.put(f"/practices/{practice_id}/swimmers/{swimmer_id}/lane", json={"lane": lane})

def get_lanes(practice_id: int) -> list[dict]:
    response = client.get(f"/practices/{practice_id}/lanes")
    assert response.status_code == 200
    return response.json()

def assigned_practice_with_swimmer() -> tuple[int, int]:
    practice_id = create_practice()
    swimmer_id = create_swimmer()
    assign(practice_id, swimmer_id)
    return practice_id, swimmer_id


# ---------- PUT lane ----------

def test_set_lane_returns_204_and_is_listed():
    practice_id, swimmer_id = assigned_practice_with_swimmer()

    response = set_lane(practice_id, swimmer_id, 3)

    assert response.status_code == 204
    assert get_lanes(practice_id) == [{"swimmer_id": swimmer_id, "lane": 3}]

def test_setting_a_new_lane_moves_the_swimmer():
    practice_id, swimmer_id = assigned_practice_with_swimmer()
    set_lane(practice_id, swimmer_id, 3)

    set_lane(practice_id, swimmer_id, 7)

    assert get_lanes(practice_id) == [{"swimmer_id": swimmer_id, "lane": 7}]

def test_null_lane_takes_swimmer_out_but_keeps_them_assigned():
    practice_id, swimmer_id = assigned_practice_with_swimmer()
    set_lane(practice_id, swimmer_id, 3)

    response = set_lane(practice_id, swimmer_id, None)

    assert response.status_code == 204
    assert get_lanes(practice_id) == []
    assigned = client.get(f"/practices/{practice_id}/swimmers").json()
    assert [s["swimmer_id"] for s in assigned] == [swimmer_id]

def test_lane_must_be_between_1_and_8():
    practice_id, swimmer_id = assigned_practice_with_swimmer()

    assert set_lane(practice_id, swimmer_id, 0).status_code == 422
    assert set_lane(practice_id, swimmer_id, 9).status_code == 422
    assert set_lane(practice_id, swimmer_id, 1).status_code == 204
    assert set_lane(practice_id, swimmer_id, 8).status_code == 204

def test_set_lane_for_unassigned_swimmer_is_404_error():
    practice_id = create_practice()
    swimmer_id = create_swimmer()

    response = set_lane(practice_id, swimmer_id, 3)

    assert response.status_code == 404
    assert response.json()["detail"] == "Swimmer is not assigned to this practice"

def test_set_lane_for_missing_practice_or_swimmer_is_404_error():
    practice_id, swimmer_id = assigned_practice_with_swimmer()

    assert set_lane(practice_id + 100, swimmer_id, 3).json()["detail"] == "Practice not found"
    assert set_lane(practice_id, swimmer_id + 100, 3).json()["detail"] == "Swimmer not found"


# ---------- GET lanes ----------

def test_lanes_start_empty():
    practice_id, _ = assigned_practice_with_swimmer()

    assert get_lanes(practice_id) == []

def test_lanes_are_sorted_by_lane_then_swimmer_id():
    practice_id = create_practice()
    ids = [create_swimmer(first_name=name) for name in ["A", "B", "C"]]
    for swimmer_id in ids:
        assign(practice_id, swimmer_id)
    set_lane(practice_id, ids[0], 5)
    set_lane(practice_id, ids[1], 2)
    set_lane(practice_id, ids[2], 2)

    assert get_lanes(practice_id) == [
        {"swimmer_id": ids[1], "lane": 2},
        {"swimmer_id": ids[2], "lane": 2},
        {"swimmer_id": ids[0], "lane": 5},
    ]

def test_lanes_only_include_that_practice():
    first, swimmer_id = assigned_practice_with_swimmer()
    second = create_practice(start_time="15:00:00", end_time="16:30:00")
    assign(second, swimmer_id)
    set_lane(first, swimmer_id, 4)

    assert get_lanes(second) == []

def test_get_lanes_for_missing_practice_is_404_error():
    response = client.get("/practices/1/lanes")

    assert response.status_code == 404
    assert response.json()["detail"] == "Practice not found"


# ---------- Lanes are cleaned up ----------

def test_unassigning_removes_the_lane():
    practice_id, swimmer_id = assigned_practice_with_swimmer()
    set_lane(practice_id, swimmer_id, 3)

    client.delete(f"/practices/{practice_id}/swimmers/{swimmer_id}")
    assign(practice_id, swimmer_id)   # assigned again, but starts with no lane

    assert get_lanes(practice_id) == []

def test_assigning_again_keeps_the_lane():
    practice_id, swimmer_id = assigned_practice_with_swimmer()
    set_lane(practice_id, swimmer_id, 3)

    assign(practice_id, swimmer_id)   # already assigned, so nothing changes

    assert get_lanes(practice_id) == [{"swimmer_id": swimmer_id, "lane": 3}]

def test_deleting_swimmer_removes_their_lane():
    practice_id, swimmer_id = assigned_practice_with_swimmer()
    set_lane(practice_id, swimmer_id, 3)

    client.delete(f"/swimmers/{swimmer_id}")

    assert get_lanes(practice_id) == []

def test_editing_practice_keeps_lanes():
    practice_id, swimmer_id = assigned_practice_with_swimmer()
    set_lane(practice_id, swimmer_id, 3)

    client.put(f"/practices/{practice_id}", json={**VALID_PRACTICE, "day": 4})

    assert get_lanes(practice_id) == [{"swimmer_id": swimmer_id, "lane": 3}]
