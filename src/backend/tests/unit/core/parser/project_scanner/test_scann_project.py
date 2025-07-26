# src/backend/tests/unit/core/parser/project_scanner/test_scan_project.py
import pytest
from app.core.parser.project_scanner import ProjectScanner
from app.db import collections
from app.core.manager import CodeGraphManager

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
    all_edges = collections.uses_import_edges.find({})
    for edge in all_edges:
        print(f"Edge: {edge.target_qname} {edge.alias} {edge.from_id} {edge.to_id} {edge.import_position.line_no}")
        from_node = collections.nodes.get(edge.from_id)
        to_node = collections.nodes.get(edge.to_id)
        print(f"  from_id qname: {getattr(from_node, 'qname', None)}")
        print(f"  to_id qname: {getattr(to_node, 'qname', None)}")
        print("")

  
    print(f"All edges: {len(all_edges)}")

    # Project (1)
    # Folders (1): models
    # Files (4): main.py, utils.py, models/user.py, models/__init__, 
    # Classes (3): MainApp, UtilityClass, User
    # Functions (7): start_app, MainApp.run, MainApp.__init__, helper_function, 
    #                UtilityClass.do_something, User.__init__, User.get_name
    assert len(all_nodes) == 1 + 5 + 3 + 7 + 1, "Should create the correct number of nodes"

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

def test_tree_structure(sample_project_path):
    """
    Tests that the tree structure is correctly created.
    """
    scanner = ProjectScanner(sample_project_path)
    scanner.scan()

    manager = CodeGraphManager()
    projects = manager.get_all_projects()
    assert len(projects) == 1

    project = projects[0]
    
    folders = project.get_folders()
    files = project.get_files()


    assert len(folders) == 1
    assert len(files) == 3
    
    models_folder = folders[0]
    assert (len(models_folder.get_files()) == 2)
    assert (len(models_folder.get_folders()) == 0)

    main_file = files[0]

    assert (len(main_file.get_functions()) == 3)
    assert (len(main_file.get_classes()) == 1)

    utils_file = files[1]

    
    assert (len(utils_file.get_functions()) == 2)
    assert (len(utils_file.get_classes()) == 1)

    utils_class = utils_file.get_classes()[0]
    assert (utils_class.name == "UtilityClass")

    helper_func = utils_file.get_functions()[0]
    assert (helper_func.name == "helper_function")
