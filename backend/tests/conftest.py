import pytest
from app.storage import swimmers, practices, assignments

@pytest.fixture(autouse=True)
def clear_storage():
    swimmers.clear()
    practices.clear()
    assignments.clear()