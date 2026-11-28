from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)

VALID_PRACTICE = {
    "day": 5,
    "start_time": "09:00:00",
    "end_time": "11:00:00",
    "practice_title": "Sp2 w/ AC",
}

def create_practice(**overrides) -> dict:
    """POST a valid swimmer, with any fields overridden, and return the response body."""
    response = client.post("/practices", json={**VALID_PRACTICE, **overrides})
    assert response.status_code == 201
    return response.json()

def test_create_practice_returns_201_and_correct_info():
    practice_one = create_practice()

    assert practice_one["day"] == 5
    assert practice_one["start_time"] == "09:00:00"
    assert practice_one["end_time"] == "11:00:00"
    assert practice_one["practice_title"] == "Sp2 w/ AC"
    assert "practice_id" in practice_one

def test_create_practice_returns_422_if_end_is_before_start():
    overrides = {"start_time": "11:00:00", "end_time": "09:00:00"}
    response = client.post("/practices", json={**VALID_PRACTICE, **overrides})

    assert response.status_code == 422

    error = response.json()["detail"][0]

    assert error["type"] == "value_error"
    assert "Start time must be before end time" in error["msg"]

def test_create_practice_returns_422_if_end_equals_start():
    overrides = {"start_time": "09:00:00", "end_time": "09:00:00"}
    response = client.post("/practices", json={**VALID_PRACTICE, **overrides})

    assert response.status_code == 422

    error = response.json()["detail"][0]

    assert error["type"] == "value_error"
    assert "Start time must be before end time" in error["msg"]

def test_get_practice_after_create():
    practice_one = create_practice()
    practice_one_id = practice_one["practice_id"]

    response = client.get(f"/practices/{practice_one_id}")

    assert response.status_code == 200

    fetched_practice_one = response.json()

    assert fetched_practice_one == practice_one
    assert fetched_practice_one["practice_id"] == practice_one_id

def test_list_all_practices():
    created_practices=[create_practice(),
                      create_practice(day=1, start_time="13:00:00", end_time="15:00:00",
                                      practice_title="Skills and Drills"),

                      create_practice(day=2, start_time="06:00:00", end_time="08:00:00",
                                      practice_title="EN1"),

                      create_practice(day=1, start_time="07:00:00", end_time="08:30:00",
                                      practice_title="IM")]
    

    response = client.get("/practices")

    assert response.status_code == 200
    assert created_practices == response.json()

def test_list_all_practices_for_a_given_day():
    created_practices=[create_practice(),
                      create_practice(day=1, start_time="13:00:00", end_time="15:00:00",
                                      practice_title="Skills and Drills"),

                      create_practice(day=2, start_time="06:00:00", end_time="08:00:00",
                                      practice_title="EN1"),

                      create_practice(day=1, start_time="07:00:00", end_time="08:30:00",
                                      practice_title="IM")]
    

    response = client.get(f"/practices?day=1")

    assert response.status_code == 200
    expected = [created_practices[1], created_practices[3]]   # the two Monday practices
    assert response.json() == expected

def test_list_practices_for_invalid_day_is_422_error():
    response = client.get("/practices", params={"day": 9})

    assert response.status_code == 422

    error = response.json()["detail"][0]

    assert error["loc"] == ["query", "day"]

def test_get_nonexisting_practice_is_404_error():
    practice_id = 1
    response = client.get(f"/practices/{practice_id}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Practice not found"

def test_delete_nonexisting_practice_is_404_error():
    practice_id = 1
    response = client.delete(f"/practices/{practice_id}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Practice not found"

def test_practice_storage_starts_empty():
    response = client.get("/practices")

    assert response.status_code == 200
    assert response.json() == []

def test_get_of_deleted_practice_is_404_error():
    practice_one = create_practice()
    practice_one_id = practice_one["practice_id"]

    deleted_response = client.delete(f"/practices/{practice_one_id}")
    assert deleted_response.status_code == 204

    response = client.get(f"/practices/{practice_one_id}")
    assert response.status_code == 404


# ---------- PUT /practices/{practice_id} ----------

def test_update_practice_changes_every_field():
    practice_id = create_practice()["practice_id"]
    new_fields = {"day": 2, "start_time": "06:00:00", "end_time": "07:30:00",
                  "practice_title": "Morning Swim"}

    response = client.put(f"/practices/{practice_id}", json=new_fields)

    assert response.status_code == 200
    assert response.json() == {**new_fields, "practice_id": practice_id}
    # The change is stored, not just echoed back
    assert client.get(f"/practices/{practice_id}").json() == response.json()

def test_update_practice_keeps_its_assignments():
    practice_id = create_practice()["practice_id"]
    swimmer = client.post("/swimmers", json={"first_name": "Austin", "last_name": "Willoughby",
                                             "weights_group": "FOUR_DAY"}).json()
    client.put(f"/practices/{practice_id}/swimmers/{swimmer['swimmer_id']}")

    client.put(f"/practices/{practice_id}", json={**VALID_PRACTICE, "day": 3})

    assigned = client.get(f"/practices/{practice_id}/swimmers").json()
    assert [s["swimmer_id"] for s in assigned] == [swimmer["swimmer_id"]]

def test_update_practice_moves_it_to_the_new_day():
    practice_id = create_practice()["practice_id"]   # created on day 5

    client.put(f"/practices/{practice_id}", json={**VALID_PRACTICE, "day": 1})

    assert client.get("/practices", params={"day": 5}).json() == []
    assert [p["practice_id"] for p in client.get("/practices", params={"day": 1}).json()] == [practice_id]

def test_update_nonexisting_practice_is_404_error():
    response = client.put("/practices/1", json=VALID_PRACTICE)

    assert response.status_code == 404
    assert response.json()["detail"] == "Practice not found"

def test_update_practice_with_end_before_start_is_422_error():
    practice_id = create_practice()["practice_id"]
    overrides = {"start_time": "11:00:00", "end_time": "09:00:00"}

    response = client.put(f"/practices/{practice_id}", json={**VALID_PRACTICE, **overrides})

    assert response.status_code == 422
    # A rejected update leaves the practice unchanged
    assert client.get(f"/practices/{practice_id}").json()["start_time"] == "09:00:00"
