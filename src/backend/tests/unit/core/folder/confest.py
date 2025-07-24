import pytest
from app.core.manager import CodeGraphManager

@pytest.fixture
def create_folder():
    manager = CodeGraphManager()
    project = manager.create_project(name="test_project", path="/path/to/project")

    folder = project.add_folder(folder_name="src", folder_path=project.absolute_path + "/")

    return folder