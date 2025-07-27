from app.core.manager import CodeGraphManager
from app.models.shared import NodePosition
from app.models.properties import TypeKeyValuesProperties


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

    input = TypeKeyValuesProperties(
        varname="input1",
        varType="int",
        position=NodePosition(
            line_no=1, 
            col_offset=23, 
            end_line_no=1, 
            end_col_offset=23
        )
    )
    function.add_input(input)

    output = TypeKeyValuesProperties(
        varname="output1",
        varType="int",
        position=NodePosition(
            line_no=1, 
            col_offset=23, 
            end_line_no=1,
            end_col_offset=23
        )
    )
    function.add_output(output)

    expected_input = {
        "varname": "input1", 
        "position": NodePosition(
            line_no=1, 
            col_offset=23, 
            end_line_no=1, 
            end_col_offset=23
        ), 
        "varType": "int"
    }
    expected_output = {
        "varname": "output1", 
        "position": NodePosition(
            line_no=1, 
            col_offset=23, 
            end_line_no=1, 
            end_col_offset=23
        ), 
        "varType": "int"
    }
    assert function.inputs[0].varname == expected_input["varname"]
    assert function.inputs[0].varType == expected_input["varType"]
    assert function.inputs[0].position == expected_input["position"]
    assert function.outputs[0].varname == expected_output["varname"]
    assert function.outputs[0].varType == expected_output["varType"]
    assert function.outputs[0].position == expected_output["position"]
    