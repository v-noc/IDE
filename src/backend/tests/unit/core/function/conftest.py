import pytest
from app.core.manager import CodeGraphManager
from app.models.shared import NodePosition

@pytest.fixture
def create_function():
    manager = CodeGraphManager()
    project = manager.create_project(name="test", path="/path/to/project")
    main_file = project.add_file(file_name="main.py", file_path=project.absolute_path + "/")
    function = main_file.add_function(name="test", 
                                      position=NodePosition(line_no=1, col_offset=23, end_line_no=1, end_col_offset=23), 
                                      inputs=[], 
                                      outputs=[])
    return function