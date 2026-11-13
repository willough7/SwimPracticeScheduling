import pytest
from app.storage import swimmers

@pytest.fixture(autouse=True)
def clear_storage():
    swimmers.clear()