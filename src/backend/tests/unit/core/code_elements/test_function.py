# src/backend/tests/unit/core/code_elements/test_function.py
from app.models.node import NodePosition
from app.db import collections as db
from app.core.code_elements import Function

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
    created_function.add_input("param1", position, type="int", default=0)

    retrieved_node = db.nodes.get(created_function.id)
    assert len(retrieved_node.properties.inputs) == 1
    input_param = retrieved_node.properties.inputs[0]
    assert input_param["name"] == "param1"
    assert input_param["type"] == "int"
    assert input_param["default"] == 0
    assert input_param["position"] == position.model_dump()

def test_add_multiple_inputs(created_function: Function):
    """Test adding multiple input parameters to a function."""
    pos1 = NodePosition(line_no=2, col_offset=4, end_line_no=2, end_col_offset=10)
    pos2 = NodePosition(line_no=2, col_offset=20, end_line_no=2, end_col_offset=26)
    created_function.add_input("param1", pos1, type="int")
    created_function.add_input("param2", pos2, type="str")

    retrieved_node = db.nodes.get(created_function.id)
    assert len(retrieved_node.properties.inputs) == 2
    assert retrieved_node.properties.inputs[0]["name"] == "param1"
    assert retrieved_node.properties.inputs[1]["name"] == "param2"

def test_add_output_to_function(created_function: Function):
    """Test adding an output/return value to a function."""
    position = NodePosition(line_no=3, col_offset=0, end_line_no=3, end_col_offset=10)
    created_function.add_output("return_value", position, type="str")

    retrieved_node = db.nodes.get(created_function.id)
    assert len(retrieved_node.properties.outputs) == 1
    output_param = retrieved_node.properties.outputs[0]
    assert output_param["name"] == "return_value"
    assert output_param["type"] == "str"
    assert output_param["position"] == position.model_dump()

def test_add_call(created_function: Function, created_class):
    """Test creating a 'calls' edge to another function or class."""
    call_position = NodePosition(line_no=10, col_offset=4, end_line_no=10, end_col_offset=20)
    created_function.add_call(created_class, position=call_position)

    # Verify the edge was created
    calls_edge = db.calls_edges.find({"_from": created_function.id, "_to": created_class.id})
    assert len(calls_edge) == 1
    assert calls_edge[0].position == call_position
