from app.core.manager import CodeGraphManager
from app.models.shared import NodePosition


def test_create_function():
    manager = CodeGraphManager()
    project = manager.create_project(name="test", path="/path/to/project")
    main_file = project.add_file(
        file_name="main.py", 
        file_path=project.absolute_path + "/"
    )
    assert len(main_file.get_functions()) == 0

    function = main_file.add_function(
        name="test", 
        position=NodePosition(
            line_no=1, 
            col_offset=23, 
            end_line_no=1, 
            end_col_offset=23
        ), 
        inputs=[], 
        outputs=[]
    )

    assert len(main_file.get_functions()) == 1
    

def test_create_function_with_inputs_and_outputs(created_function):
    function = created_function
    assert function.inputs == []
    assert function.outputs == []

    function.add_input(
        name="input1", 
        position=NodePosition(
            line_no=1, 
            col_offset=23, 
            end_line_no=1, 
            end_col_offset=23
        ), 
        type="int"
    )  
    function.add_output(
        name="output1", 
        position=NodePosition(
            line_no=1, 
            col_offset=23, 
            end_line_no=1, 
            end_col_offset=23
        ), 
        type="int"
    )

    expected_input = {
        "name": "input1", 
        "position": NodePosition(
            line_no=1, 
            col_offset=23, 
            end_line_no=1, 
            end_col_offset=23
        ), 
        "type": "int"
    }
    expected_output = {
        "name": "output1", 
        "position": NodePosition(
            line_no=1, 
            col_offset=23, 
            end_line_no=1, 
            end_col_offset=23
        ), 
        "type": "int"
    }
    assert function.inputs == [expected_input]
    assert function.outputs == [expected_output]