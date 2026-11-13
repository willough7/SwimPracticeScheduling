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




    