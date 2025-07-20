# tests/e2e/test_graph_builder.py

from app.core.manager import CodeGraphManager
from app.db import collections as db
import os

def test_graph_builder_creates_correct_structure(temp_project_dir):
    """
    Tests that the CodeGraphManager and Project domain objects correctly
    create nodes and edges for a simple project structure.
    """
    # 1. Arrange: Instantiate the manager
    manager = CodeGraphManager()
    project_name = os.path.basename(temp_project_dir)

    # 2. Act: Create the project and its structure
    project = manager.create_project(name=project_name, path=temp_project_dir)
    utils_folder = project.add_folder(folder_name="utils", folder_path=os.path.join(temp_project_dir, "utils"))
    main_py_file = project.add_file(file_name="main.py", file_path=os.path.join(temp_project_dir, "main.py"))
    helpers_py_file = utils_folder.add_file(file_name="helpers.py", file_path=os.path.join(temp_project_dir, "utils", "helpers.py"))

    # 3. Assert: Query the database and validate the graph
    
    # Find the project node
    project_node = db.nodes.get(project.key)
    assert project_node is not None
    assert project_node.name == project_name

    # Find the folder and file nodes
    main_py_node = db.nodes.get(main_py_file.key)
    utils_folder_node = db.nodes.get(utils_folder.key)
    helpers_py_node = db.nodes.get(helpers_py_file.key)
    
    assert main_py_node is not None
    assert utils_folder_node is not None
    assert helpers_py_node is not None

    # Check 'contains' edges for structure
    # Project -> main.py
    assert db.contains_edges.find({"_from": project_node.id, "_to": main_py_node.id}, limit=1)
    # Project -> utils/
    assert db.contains_edges.find({"_from": project_node.id, "_to": utils_folder_node.id}, limit=1)
    # utils/ -> helpers.py
    assert db.contains_edges.find({"_from": utils_folder_node.id, "_to": helpers_py_node.id}, limit=1)
    
    # Clean up created data
    db.nodes.truncate()
    db.contains_edges.truncate()
    db.calls_edges.truncate()
    db.uses_import_edges.truncate()
    db.implements_edges.truncate()
    db.belongs_to_edges.truncate()
