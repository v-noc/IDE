import pytest
from app.core.manager import CodeGraphManager

@pytest.fixture
def create_project():
    manager = CodeGraphManager()
    project = manager.create_project(name="test", path="/path/to/project")
    return project