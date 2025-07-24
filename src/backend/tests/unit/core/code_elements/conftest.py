# src/backend/tests/unit/core/code_elements/conftest.py
import pytest
from app.models import node
from app.db import collections as db
from app.core.code_elements import Function, Class


@pytest.fixture
def sample_function_node():
    """Returns a sample FunctionNode model."""
    return node.FunctionNode(
        name="test_func",
        qname="test_project.test_module.test_func",
        node_type="function",
        properties=node.FunctionProperties(
            position=node.NodePosition(
                line_no=1, 
                col_offset=0, 
                end_line_no=2, 
                end_col_offset=0
            )
        )
    )

@pytest.fixture
def sample_class_node():
    """Returns a sample ClassNode model."""
    return node.ClassNode(
        name="TestClass",
        qname="test_project.test_module.TestClass",
        node_type="class",
        properties=node.ClassProperties(
            position=node.NodePosition(
                line_no=5, 
                col_offset=0, 
                end_line_no=10, 
                end_col_offset=0
            )
        )
    )

@pytest.fixture
def created_function(sample_function_node):
    """Creates and returns a Function domain object."""
    created_node = db.nodes.create(sample_function_node)
    return Function(created_node)

@pytest.fixture
def created_class(sample_class_node):
    """Creates and returns a Class domain object."""
    created_node = db.nodes.create(sample_class_node)
    return Class(created_node)
