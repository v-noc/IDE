# src/backend/tests/unit/core/code_elements/test_class.py
from app.models.node import NodePosition
from app.db import collections as db
from app.core.code_elements import Class

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
    created_class.add_field("field1", position, type="str", default="'hello'")

    retrieved_node = db.nodes.get(created_class.id)
    assert len(retrieved_node.properties.fields) == 1
    field = retrieved_node.properties.fields[0]
    assert field["name"] == "field1"
    assert field["type"] == "str"
    assert field["default"] == "'hello'"
    assert field["position"] == position.model_dump()

def test_add_multiple_fields(created_class: Class):
    """Test adding multiple fields to a class."""
    pos1 = NodePosition(line_no=6, col_offset=4, end_line_no=6, end_col_offset=20)
    pos2 = NodePosition(line_no=7, col_offset=4, end_line_no=7, end_col_offset=20)
    created_class.add_field("field1", pos1, type="str")
    created_class.add_field("field2", pos2, type="int")

    retrieved_node = db.nodes.get(created_class.id)
    assert len(retrieved_node.properties.fields) == 2
    assert retrieved_node.properties.fields[0]["name"] == "field1"
    assert retrieved_node.properties.fields[1]["name"] == "field2"

def test_add_method_to_class(created_class: Class):
    """Test adding a method to a class."""
    method_pos = NodePosition(line_no=8, col_offset=4, end_line_no=9, end_col_offset=20)
    method_func = created_class.add_method("new_method", method_pos)

    # Verify the function node was created
    retrieved_func_node = db.nodes.get(method_func.id)
    assert retrieved_func_node is not None
    assert retrieved_func_node.name == "new_method"
    assert retrieved_func_node.qname == "test_project.test_module.TestClass::new_method"

    # Verify the 'implements' edge was created
    implements_edge = db.implements_edges.find({"_from": created_class.id, "_to": method_func.id})
    assert len(implements_edge) == 1
