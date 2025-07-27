# Basic project scanning functionality tests
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
    # all_edges = collections.uses_import_edges.find({})
    # for edge in all_edges:
    #     edge_info = (
    #         f"Edge: {edge.target_qname} {edge.alias} {edge.from_id} " 
    #         f"{edge.to_id} {edge.import_position.line_no}"
    #     )
    #     print(edge_info)
    #     from_node = collections.nodes.get(edge.from_id)
    #     to_node = collections.nodes.get(edge.to_id)
    #     print(f"  from_id qname: {getattr(from_node, 'qname', None)}")
    #     to_qname = getattr(to_node, 'qname', None)
    #     to_json = to_node.model_dump_json()
    #     print(f"  to_id qname: {to_qname} {to_json}")
    #     print("")

    # Project (1)
    # Folders (1): models
    # Files (4): main.py, utils.py, models/user.py, models/__init__, 
    # Classes (3): MainApp, UtilityClass, User
    # Functions (7): start_app, MainApp.run, MainApp.__init__, helper_function, 
    #                UtilityClass.do_something, User.__init__, User.get_name
    expected_nodes = 1 + 5 + 3 + 7 + 1
    assert len(all_nodes) == expected_nodes, (
        "Should create the correct number of nodes"
    )

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

    user_get_name_qname = "models.user.User.get_name"
    user_get_name_node = collections.nodes.find_one(
        {"qname": user_get_name_qname}
    )
    assert user_get_name_node is not None
    assert user_get_name_node.node_type == "function"
    
    helper_func_qname = "utils.helper_function"
    helper_func_node = collections.nodes.find_one(
        {"qname": helper_func_qname}
    )
    assert helper_func_node is not None
    assert helper_func_node.node_type == "function"


def test_scan_summary_information(sample_project_path):
    """
    Test that scan summary provides useful information.
    """
    scanner = ProjectScanner(sample_project_path)
    scanner.scan()
    
    summary = scanner.get_scan_summary()
    
    assert "project_path" in summary
    assert "total_symbols" in summary
    assert "created_packages" in summary
    
    assert summary["total_symbols"] > 5, (
        "Should track symbols in sample project"
    )
    
    print(f"Scan summary: {summary}")


def test_package_node_creation(sample_project_path):
    """
    Test that external package nodes are created for imports.
    """
    scanner = ProjectScanner(sample_project_path)
    scanner.scan()
    
    # Should create package nodes for external imports
    package_nodes = collections.nodes.find({"node_type": "package"})
    assert len(package_nodes) > 0, "Should create package nodes"
    
    # Check for pydantic package from sample project
    package_qnames = [node.qname for node in package_nodes]
    assert any("pydantic" in qname for qname in package_qnames), (
        "Should find pydantic package from sample project imports"
    )