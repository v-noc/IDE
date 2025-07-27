# Complex project specific tests
import pytest
from app.core.parser.project_scanner import ProjectScanner
from app.db import collections
from app.core.code_elements import Class

# Marks all tests in this file as using the 'clear_db' fixture
pytestmark = pytest.mark.usefixtures("clear_db")


def test_complex_project_structure_and_imports(complex_project_path):
    """
    Test complex project with nested folders, various import patterns,
    and comprehensive structure analysis.
    """
    scanner = ProjectScanner(str(complex_project_path))
    scanner.scan()

    # Get all nodes for analysis
    all_nodes = collections.nodes.find({"node_type": "class"})
    for node in all_nodes:
        class_obj = Class(node)
        print(f"class_obj.name: {class_obj.name}")
        print(f"class_obj.methods: {len(class_obj.methods)}")
    