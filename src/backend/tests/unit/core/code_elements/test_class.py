# src/backend/tests/unit/core/code_elements/test_class.py
from app.models.node import FunctionNode, NodePosition
from app.db import collections as db
from app.core.code_elements import Class, Function
from app.models.properties import FunctionProperties, TypeKeyValuesProperties

def test_create_class(created_class):
    """Test creation of a Class domain object."""
    assert created_class is not None
    assert created_class.model.name == "TestClass"
    retrieved_node = db.nodes.get(created_class.id)
    assert retrieved_node is not None
    assert retrieved_node.name == "TestClass"

def test_add_field_to_class(created_class: Class):
    """Test adding a field to a class."""
    position = NodePosition(line_no=6, col_offset=4, end_line_no=6, end_col_offset=20)
    field = TypeKeyValuesProperties(
        varname="field1",
        varType="str",
        position=position
    )
    print(created_class.add_field)
    created_class.add_field(field)

    retrieved_node = db.nodes.get(created_class.id)
    assert len(retrieved_node.properties.fields) == 1
    assert retrieved_node.properties.fields[0].varname == "field1"
    assert retrieved_node.properties.fields[0].varType == "str"
    assert retrieved_node.properties.fields[0].position == position

def test_add_multiple_fields(created_class: Class):
    """Test adding multiple fields to a class."""
    pos1 = NodePosition(line_no=6, col_offset=4, end_line_no=6, end_col_offset=20)
    pos2 = NodePosition(line_no=7, col_offset=4, end_line_no=7, end_col_offset=20)
    field1 = TypeKeyValuesProperties(
        varname="field1",
        varType="str",
        position=pos1
    )
    field2 = TypeKeyValuesProperties(
        varname="field2",
        varType="int",
        position=pos2)
    created_class.add_field(field1)
    created_class.add_field(field2)

    retrieved_node = db.nodes.get(created_class.id)
    assert len(retrieved_node.properties.fields) == 2
    assert retrieved_node.properties.fields[0].varname == "field1"
    assert retrieved_node.properties.fields[0].varType == "str"
    assert retrieved_node.properties.fields[0].position == pos1
    assert retrieved_node.properties.fields[1].varname == "field2"
    assert retrieved_node.properties.fields[1].varType == "int"
    assert retrieved_node.properties.fields[1].position == pos2

def test_add_method_to_class(created_class: Class):
    """Test adding a method to a class."""
    method_pos = NodePosition(line_no=8, col_offset=4, end_line_no=9, end_col_offset=20)

    method_func = FunctionNode(
        name="new_method",
        qname="test_project.test_module.TestClass::new_method",
        properties=FunctionProperties(
            position=method_pos
        )
    )
    method_func = db.nodes.create(method_func)
    created_class.add_method(method_func.id)

    # Verify the function node was created
    retrieved_func_node = db.nodes.get(method_func.id)
    assert retrieved_func_node is not None
    assert retrieved_func_node.name == "new_method"
    assert retrieved_func_node.qname == "test_project.test_module.TestClass::new_method"

    # Verify the 'implements' edge was created
    implements_edge = db.implements_edges.find({"_from": created_class.id, "_to": method_func.id})
    assert len(implements_edge) == 1
