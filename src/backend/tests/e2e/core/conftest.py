import pytest
from app.core.manager import CodeGraphManager


@pytest.fixture(scope="function")
def manager():
    """
    Provides a CodeGraphManager instance for each test function,
    ensuring a clean state.
    """
    m = CodeGraphManager()
    # Clean up any projects that might be left over from previous runs
    for p in m.get_all_projects():
        m.delete_project(p.key)
    return m 