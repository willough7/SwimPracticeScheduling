import pytest
from app import auth
from app.main import app
from app.storage import swimmers, practices, assignments, lanes

@pytest.fixture(autouse=True)
def clear_storage():
    swimmers.clear()
    practices.clear()
    assignments.clear()
    lanes.clear()
    auth.sessions.clear()

@pytest.fixture(autouse=True)
def logged_in_as_admin(request):
    """Most tests check what the API does, not who's allowed to do it, so they
    run as if an admin is logged in: require_admin is swapped for a stand-in
    that always says yes. Tests marked @pytest.mark.real_login (the login tests)
    skip this and go through the real check."""
    if (request.node.get_closest_marker("real_login")):
        yield
        return
    app.dependency_overrides[auth.require_admin] = lambda: "test-admin"
    yield
    app.dependency_overrides.clear()
