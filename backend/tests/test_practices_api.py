from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)

VALID_PRACTICE = {
    "day": 5,
    "start_time": "09:00:00",
    "end_time": "11:00:00",
    "practice_title": "Sp2 w/ AC",
    "is_morning": True
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
    assert practice_one["is_morning"] == True
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
                                      practice_title="Skills and Drills", is_morning=False),

                      create_practice(day=2, start_time="06:00:00", end_time="08:00:00",
                                      practice_title="EN1", is_morning=True),

                      create_practice(day=1, start_time="07:00:00", end_time="08:30:00",
                                      practice_title="IM", is_morning=True)]
    

    response = client.get("/practices")

    assert response.status_code == 200
    assert created_practices == response.json()

def test_list_all_practices_for_a_given_day():
    created_practices=[create_practice(),
                      create_practice(day=1, start_time="13:00:00", end_time="15:00:00",
                                      practice_title="Skills and Drills", is_morning=False),

                      create_practice(day=2, start_time="06:00:00", end_time="08:00:00",
                                      practice_title="EN1", is_morning=True),

                      create_practice(day=1, start_time="07:00:00", end_time="08:30:00",
                                      practice_title="IM", is_morning=True)]
    

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