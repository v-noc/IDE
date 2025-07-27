# src/backend/tests/unit/core/code_elements/test_function.py
from app.models.node import NodePosition
from app.db import collections as db
from app.core.code_elements import Function
from app.models.properties import TypeKeyValuesProperties

def test_create_function(created_function):
    """Test creation of a Function domain object."""
    assert created_function is not None
    assert created_function.model.name == "test_func"
    retrieved_node = db.nodes.get(created_function.id)
    assert retrieved_node is not None
    assert retrieved_node.name == "test_func"

def test_add_input_to_function(created_function: Function):
    """Test adding an input parameter to a function."""
    position = NodePosition(line_no=2, col_offset=4, end_line_no=2, end_col_offset=10)
    input = TypeKeyValuesProperties(
        varname="param1",
        varType="int",
        position=position
    )
    created_function.add_input(input)

    retrieved_node = db.nodes.get(created_function.id)
    assert len(retrieved_node.properties.inputs) == 1
    input_param = retrieved_node.properties.inputs[0]
    assert input_param.varname == "param1"
    assert input_param.varType == "int"
    assert input_param.position == position

def test_add_multiple_inputs(created_function: Function):
    """Test adding multiple input parameters to a function."""
    pos1 = NodePosition(line_no=2, col_offset=4, end_line_no=2, end_col_offset=10)
    pos2 = NodePosition(line_no=2, col_offset=20, end_line_no=2, end_col_offset=26)
    input1 = TypeKeyValuesProperties(
        varname="param1",
        varType="int",
        position=pos1
    )
    input2 = TypeKeyValuesProperties(
        varname="param2",
        varType="str",
        position=pos2
    )
    created_function.add_input(input1)
    created_function.add_input(input2)

    retrieved_node = db.nodes.get(created_function.id)
    assert len(retrieved_node.properties.inputs) == 2
    assert retrieved_node.properties.inputs[0].varname == "param1"
    assert retrieved_node.properties.inputs[1].varname == "param2"

def test_add_output_to_function(created_function: Function):
    """Test adding an output/return value to a function."""
    position = NodePosition(line_no=3, col_offset=0, end_line_no=3, end_col_offset=10)
    output = TypeKeyValuesProperties(
        varname="return_value",
        varType="str",
        position=position
    )
    created_function.add_output(output)

    retrieved_node = db.nodes.get(created_function.id)
    assert len(retrieved_node.properties.outputs) == 1
    output_param = retrieved_node.properties.outputs[0]
    assert output_param.varname == "return_value"
    assert output_param.varType == "str"
    assert output_param.position == position

def test_add_call(created_function: Function, created_class):
    """Test creating a 'calls' edge to another function or class."""
    call_position = NodePosition(line_no=10, col_offset=4, end_line_no=10, end_col_offset=20)
    created_function.add_call(created_class, position=call_position)

    # Verify the edge was created
    calls_edge = db.calls_edges.find({"_from": created_function.id, "_to": created_class.id})
    assert len(calls_edge) == 1
    assert calls_edge[0].position == call_position
