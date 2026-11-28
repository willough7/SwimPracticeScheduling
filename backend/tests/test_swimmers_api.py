from pathlib import Path

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

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

def test_create_swimmer_returns_201_and_correct_info():
    swimmer_one = create_swimmer()

    assert swimmer_one["first_name"] == "Austin"
    assert swimmer_one["last_name"] == "Willoughby"
    assert swimmer_one["weights_group"] == "FOUR_DAY"
    assert set(swimmer_one["tags"]) == {"100s", "Sprint"}
    assert "swimmer_id" in swimmer_one

def test_get_swimmer_after_create():
    swimmer_one = create_swimmer()
    swimmer_one_id = swimmer_one["swimmer_id"]

    response = client.get(f"/swimmers/{swimmer_one_id}")

    assert response.status_code == 200

    fetched_swimmer_one = response.json()

    assert fetched_swimmer_one == swimmer_one
    assert fetched_swimmer_one["swimmer_id"] == swimmer_one_id

def test_list_all_swimmers():
    created_swimmers=[create_swimmer(),
                      create_swimmer(first_name="Jeremias", last_name="Pock",
                                     weights_group="THREE_DAY_A", tags=["IM","Breast"]),

                      create_swimmer(first_name="Terry", last_name="Lee",
                                     weights_group="THREE_DAY_A", tags=["IM"]),

                      create_swimmer(first_name="Emmitt", last_name="Shank",
                                     weights_group="THREE_DAY_B", tags=["Distance"])]
    

    response = client.get("/swimmers")

    assert response.status_code == 200
    assert created_swimmers == response.json()

def test_get_nonexisting_swimmer_is_404_error():
    swimmer_id = 1
    response = client.get(f"/swimmers/{swimmer_id}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Swimmer not found"

def test_delete_nonexisting_swimmer_is_404_error():
        swimmer_id = 1
        response = client.delete(f"/swimmers/{swimmer_id}")

        assert response.status_code == 404
        assert response.json()["detail"] == "Swimmer not found"

def test_invalid_weights_group_is_422_error():
    overrides = {"weights_group": "megaLifter"}
    response = client.post("/swimmers", json={**VALID_SWIMMER, **overrides})
    
    assert response.status_code == 422

def test_empy_name_is_422_error():
    overrides = {"first_name": ""}
    response = client.post("/swimmers", json={**VALID_SWIMMER, **overrides})
    
    assert response.status_code == 422

def test_swimmer_storage_starts_empty():
    response = client.get("/swimmers")

    assert response.status_code == 200
    assert response.json() == []

def test_get_of_deleted_swimmer_is_404_error():
    swimmer_one = create_swimmer()
    swimmer_one_id = swimmer_one["swimmer_id"]

    deleted_response = client.delete(f"/swimmers/{swimmer_one_id}")
    assert deleted_response.status_code == 204

    response = client.get(f"/swimmers/{swimmer_one_id}")
    assert response.status_code == 404

def test_swimmer_does_not_have_ics():
    swimmer_one = create_swimmer()
    assert swimmer_one["has_schedule"] is False


# ---------- PUT /swimmers/{swimmer_id} ----------

SAMPLE_ICS = (Path(__file__).parent / "fixtures" / "sample_schedule.ics").read_bytes()

def test_update_swimmer_changes_their_details():
    swimmer_id = create_swimmer()["swimmer_id"]
    new_details = {"first_name": "Jeremias", "last_name": "Pock",
                   "weights_group": "THREE_DAY_B", "tags": ["IM"]}

    response = client.put(f"/swimmers/{swimmer_id}", json=new_details)

    assert response.status_code == 200
    updated = response.json()
    assert updated["swimmer_id"] == swimmer_id
    assert updated["first_name"] == "Jeremias"
    assert updated["last_name"] == "Pock"
    assert updated["weights_group"] == "THREE_DAY_B"
    assert updated["tags"] == ["IM"]
    # The change is stored, not just echoed back
    assert client.get(f"/swimmers/{swimmer_id}").json() == updated

def test_update_swimmer_keeps_their_calendar():
    swimmer_id = create_swimmer()["swimmer_id"]
    upload = client.put(f"/swimmers/{swimmer_id}/schedule",
                        files={"file": ("schedule.ics", SAMPLE_ICS, "text/calendar")})
    assert upload.status_code == 200

    response = client.put(f"/swimmers/{swimmer_id}", json={**VALID_SWIMMER, "first_name": "Renamed"})

    assert response.status_code == 200
    assert response.json()["has_schedule"] is True

def test_update_swimmer_keeps_their_assignments():
    swimmer_id = create_swimmer()["swimmer_id"]
    practice = client.post("/practices", json={"day": 2, "start_time": "06:00:00",
                                               "end_time": "08:00:00"}).json()
    client.put(f"/practices/{practice['practice_id']}/swimmers/{swimmer_id}")

    client.put(f"/swimmers/{swimmer_id}", json={**VALID_SWIMMER, "weights_group": "THREE_DAY_A"})

    assigned = client.get(f"/practices/{practice['practice_id']}/swimmers").json()
    assert [s["swimmer_id"] for s in assigned] == [swimmer_id]

def test_update_nonexisting_swimmer_is_404_error():
    response = client.put("/swimmers/1", json=VALID_SWIMMER)

    assert response.status_code == 404
    assert response.json()["detail"] == "Swimmer not found"

def test_update_swimmer_with_empty_name_is_422_error():
    swimmer_id = create_swimmer()["swimmer_id"]

    response = client.put(f"/swimmers/{swimmer_id}", json={**VALID_SWIMMER, "first_name": ""})

    assert response.status_code == 422
    # A rejected update leaves the swimmer unchanged
    assert client.get(f"/swimmers/{swimmer_id}").json()["first_name"] == "Austin"
