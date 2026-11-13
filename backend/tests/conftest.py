import pytest
from app.storage import swimmers, practices

@pytest.fixture(autouse=True)
def clear_storage():
    swimmers.clear()
    practices.clear()    