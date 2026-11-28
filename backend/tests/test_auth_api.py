"""Tests for admin login and for which routes need it.

These use the real login check (marked real_login), unlike the rest of the
suite, which runs as if an admin were always logged in. Each test gets its own
admins.json in a temporary folder, so real accounts are never touched.
"""

import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import auth, admin_accounts
from app.main import app

pytestmark = pytest.mark.real_login

PASSWORD = "correct horse battery"
SAMPLE_ICS = (Path(__file__).parent / "fixtures" / "sample_schedule.ics").read_bytes()
VALID_SWIMMER = {"first_name": "Austin", "last_name": "Willoughby", "weights_group": "FOUR_DAY"}
VALID_PRACTICE = {"day": 2, "start_time": "06:00:00", "end_time": "07:30:00",
                  "practice_title": "Morning Swim"}


@pytest.fixture(autouse=True)
def admin_account(tmp_path, monkeypatch):
    monkeypatch.setattr(admin_accounts, "ADMINS_FILE", tmp_path / "admins.json")
    # TestClient talks plain http, and browsers (and httpx) don't send Secure
    # cookies over plain http to a host that isn't localhost
    monkeypatch.setattr(auth, "COOKIE_SECURE", False)
    admin_accounts.set_password("Admin", PASSWORD)

def admin_client() -> TestClient:
    """A client (like a browser) that has logged in as the admin."""
    client = TestClient(app)
    response = client.post("/auth/login", json={"username": "admin", "password": PASSWORD})
    assert response.status_code == 200
    return client

def viewer_client() -> TestClient:
    """A client that never logs in."""
    return TestClient(app)


# ---------- Logging in and out ----------

def test_nobody_is_logged_in_at_first():
    assert viewer_client().get("/auth/me").json() == {"username": None}

def test_login_returns_the_admin_and_remembers_them():
    client = TestClient(app)

    response = client.post("/auth/login", json={"username": "admin", "password": PASSWORD})

    assert response.status_code == 200
    assert response.json() == {"username": "admin"}
    assert client.get("/auth/me").json() == {"username": "admin"}

def test_login_cookie_is_httponly_and_samesite_strict():
    response = TestClient(app).post("/auth/login", json={"username": "admin", "password": PASSWORD})

    cookie = response.headers["set-cookie"].lower()
    assert cookie.startswith(f"{auth.SESSION_COOKIE}=")
    assert "httponly" in cookie
    assert "samesite=strict" in cookie

def test_username_ignores_case_and_spaces():
    response = TestClient(app).post("/auth/login", json={"username": "  ADMIN ", "password": PASSWORD})

    assert response.status_code == 200
    assert response.json() == {"username": "admin"}

def test_wrong_password_and_unknown_username_get_the_same_answer():
    wrong_password = TestClient(app).post("/auth/login", json={"username": "admin", "password": "nope"})
    unknown_user = TestClient(app).post("/auth/login", json={"username": "nobody", "password": PASSWORD})

    assert wrong_password.status_code == unknown_user.status_code == 401
    assert wrong_password.json() == unknown_user.json() == {"detail": "Wrong username or password"}

def test_logout_ends_the_session():
    client = admin_client()

    assert client.post("/auth/logout").status_code == 204

    assert client.get("/auth/me").json() == {"username": None}
    assert client.post("/swimmers", json=VALID_SWIMMER).status_code == 401

def test_old_cookie_stops_working_after_logout():
    client = admin_client()
    token = client.cookies.get(auth.SESSION_COOKIE)
    client.post("/auth/logout")

    stolen = TestClient(app, cookies={auth.SESSION_COOKIE: token})

    assert stolen.get("/auth/me").json() == {"username": None}

def test_expired_session_is_logged_out():
    client = admin_client()
    for key, (username, _) in list(auth.sessions.items()):
        auth.sessions[key] = (username, time.time() - 1)   # pretend 12 hours have passed

    assert client.get("/auth/me").json() == {"username": None}
    assert client.post("/swimmers", json=VALID_SWIMMER).status_code == 401

def test_made_up_cookie_is_ignored():
    client = TestClient(app, cookies={auth.SESSION_COOKIE: "made-up-token"})

    assert client.get("/auth/me").json() == {"username": None}

def test_wrong_passwords_never_lock_the_account():
    # No lockout, on purpose: after many wrong tries the right password still works
    client = TestClient(app)
    for _ in range(10):
        assert client.post("/auth/login", json={"username": "admin", "password": "wrong"}).status_code == 401

    response = client.post("/auth/login", json={"username": "admin", "password": PASSWORD})

    assert response.status_code == 200


# ---------- What viewers (not logged in) can and can't do ----------

def test_viewer_can_read_everything():
    admin = admin_client()
    swimmer_id = admin.post("/swimmers", json=VALID_SWIMMER).json()["swimmer_id"]
    practice_id = admin.post("/practices", json=VALID_PRACTICE).json()["practice_id"]
    viewer = viewer_client()

    for path in ["/swimmers", f"/swimmers/{swimmer_id}", "/practices", f"/practices/{practice_id}",
                 f"/practices/{practice_id}/swimmers", f"/practices/{practice_id}/lanes",
                 f"/swimmers/{swimmer_id}/practices", "/export/week.xlsx",
                 f"/practices/{practice_id}/conflicts?week=2026-11-23"]:
        assert viewer.get(path).status_code == 200, path

def test_viewer_can_upload_a_swimmers_calendar():
    swimmer_id = admin_client().post("/swimmers", json=VALID_SWIMMER).json()["swimmer_id"]

    response = viewer_client().put(f"/swimmers/{swimmer_id}/schedule",
                                   files={"file": ("schedule.ics", SAMPLE_ICS, "text/calendar")})

    assert response.status_code == 200
    assert response.json()["has_schedule"] is True

def test_viewer_cannot_create_edit_or_delete():
    admin = admin_client()
    swimmer_id = admin.post("/swimmers", json=VALID_SWIMMER).json()["swimmer_id"]
    practice_id = admin.post("/practices", json=VALID_PRACTICE).json()["practice_id"]
    viewer = viewer_client()

    attempts = [
        viewer.post("/swimmers", json=VALID_SWIMMER),
        viewer.put(f"/swimmers/{swimmer_id}", json=VALID_SWIMMER),
        viewer.delete(f"/swimmers/{swimmer_id}"),
        viewer.post("/practices", json=VALID_PRACTICE),
        viewer.put(f"/practices/{practice_id}", json=VALID_PRACTICE),
        viewer.delete(f"/practices/{practice_id}"),
        viewer.put(f"/practices/{practice_id}/swimmers/{swimmer_id}"),
        viewer.delete(f"/practices/{practice_id}/swimmers/{swimmer_id}"),
        viewer.put(f"/practices/{practice_id}/swimmers/{swimmer_id}/lane", json={"lane": 1}),
    ]

    for response in attempts:
        assert response.status_code == 401, response.request.url
        assert response.json() == {"detail": "Admin login required"}
    # and nothing changed
    assert len(viewer.get("/swimmers").json()) == 1
    assert len(viewer.get("/practices").json()) == 1

def test_admin_can_create_edit_assign_and_delete():
    admin = admin_client()

    swimmer = admin.post("/swimmers", json=VALID_SWIMMER)
    practice = admin.post("/practices", json=VALID_PRACTICE)
    assert swimmer.status_code == practice.status_code == 201
    swimmer_id, practice_id = swimmer.json()["swimmer_id"], practice.json()["practice_id"]

    assert admin.put(f"/swimmers/{swimmer_id}", json=VALID_SWIMMER).status_code == 200
    assert admin.put(f"/practices/{practice_id}", json=VALID_PRACTICE).status_code == 200
    assert admin.put(f"/practices/{practice_id}/swimmers/{swimmer_id}").status_code == 204
    assert admin.put(f"/practices/{practice_id}/swimmers/{swimmer_id}/lane",
                     json={"lane": 2}).status_code == 204
    assert admin.delete(f"/practices/{practice_id}/swimmers/{swimmer_id}").status_code == 204
    assert admin.delete(f"/swimmers/{swimmer_id}").status_code == 204
    assert admin.delete(f"/practices/{practice_id}").status_code == 204


# ---------- Admin accounts file ----------

def test_passwords_are_not_stored_in_plain_text():
    stored = admin_accounts.ADMINS_FILE.read_text()

    assert PASSWORD not in stored
    assert '"admin": "scrypt$' in stored

def test_same_password_gets_a_different_hash_each_time():
    # thanks to the random salt
    assert admin_accounts.hash_password(PASSWORD) != admin_accounts.hash_password(PASSWORD)

def test_short_passwords_are_rejected():
    with pytest.raises(ValueError):
        admin_accounts.set_password("assistant", "short")

def test_removed_admin_cannot_log_in():
    admin_accounts.remove_account("admin")

    response = TestClient(app).post("/auth/login", json={"username": "admin", "password": PASSWORD})

    assert response.status_code == 401
