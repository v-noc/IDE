# src/backend/tests/unit/core/parser/project_scanner/test_scan_project.py
import pytest
from app.core.parser.project_scanner import ProjectScanner
from app.db import collections

# Marks all tests in this file as using the 'clear_db' fixture
pytestmark = pytest.mark.usefixtures("clear_db")

def test_scan_project_declaration_pass(sample_project_path):
    """
    Tests that the declaration pass correctly creates nodes for all files,
    classes, and functions in the sample project.
    """
    # 1. Setup
    scanner = ProjectScanner(sample_project_path)

    # 2. Action
    scanner.scan()

    # 3. Assertions
    # Check that the correct nodes were created
    all_nodes = collections.nodes.find({})
    for node in all_nodes:
        print(node.qname," ",node.node_type," ",node.name)
    # Project (1)
    # Files (4): main.py, utils.py, models/user.py, models/__init__, 
    # Classes (3): MainApp, UtilityClass, User
    # Functions (7): start_app, MainApp.run, MainApp.__init__, helper_function, 
    #                UtilityClass.do_something, User.__init__, User.get_name
    assert len(all_nodes) == 1 + 5 + 3 + 7, "Should create the correct number of nodes"

    # Find specific nodes by their qualified name (qname)
    main_app_node = collections.nodes.find_one({"qname": "main.MainApp"})
    assert main_app_node is not None
    assert main_app_node.node_type == "class"

    start_app_node = collections.nodes.find_one({"qname": "main.start_app"})
    assert start_app_node is not None
    assert start_app_node.node_type == "function"

    user_class_node = collections.nodes.find_one({"qname": "models.user.User"})
    assert user_class_node is not None
    assert user_class_node.node_type == "class"

    user_get_name_node = collections.nodes.find_one({"qname": "models.user.User.get_name"})
    assert user_get_name_node is not None
    assert user_get_name_node.node_type == "function"
    
    helper_func_node = collections.nodes.find_one({"qname": "utils.helper_function"})
    assert helper_func_node is not None
    assert helper_func_node.node_type == "function"
