# tests/e2e/test_graph_creation.py

from app.core.manager import CodeGraphManager
from app.db import collections as db
from app.models import node
import os

def test_graph_creation(temp_project_dir):
    """
    Tests that the CodeGraphManager and domain objects correctly create a
    simple graph structure.
    """
    # 1. Arrange
    manager = CodeGraphManager()
    project_name = os.path.basename(temp_project_dir)
    
    # Define positions for code elements
    class_pos = node.NodePosition(line_no=1, col_offset=0, end_line_no=5, end_col_offset=10)
    func_pos = node.NodePosition(line_no=6, col_offset=0, end_line_no=8, end_col_offset=20)

    # 2. Act
    # Create project, folder, and file
    project = manager.create_project(name=project_name, path=temp_project_dir)
    src_folder = project.add_folder(folder_name="src", folder_path=os.path.join(temp_project_dir, "src"))
    main_file = src_folder.add_file(file_name="main.py", file_path=os.path.join(temp_project_dir, "src", "main.py"))
    
    # Add class and function to the file
    my_class = main_file.add_class(name="MyClass", position=class_pos)
    my_func = main_file.add_function(name="my_function", position=func_pos)

    # 3. Assert
    # Verify project, folder, and file nodes
    project_node = db.nodes.get(project.key)
    assert project_node is not None
    assert project_node.name == project_name

    src_folder_node = db.nodes.get(src_folder.key)
    assert src_folder_node is not None
    assert src_folder_node.name == "src"

    main_file_node = db.nodes.get(main_file.key)
    assert main_file_node is not None
    assert main_file_node.name == "main.py"

    # Verify class and function nodes
    my_class_node = db.nodes.get(my_class.key)
    assert my_class_node is not None
    assert my_class_node.name == "MyClass"

    my_func_node = db.nodes.get(my_func.key)
    assert my_func_node is not None
    assert my_func_node.name == "my_function"

    # Verify 'contains' edges
    assert db.contains_edges.find({"_from": project.id, "_to": src_folder.id}, limit=1)
    assert db.contains_edges.find({"_from": src_folder.id, "_to": main_file.id}, limit=1)
    assert db.contains_edges.find({"_from": main_file.id, "_to": my_class.id}, limit=1)
    assert db.contains_edges.find({"_from": main_file.id, "_to": my_func.id}, limit=1)

    # 4. Teardown
    db.nodes.truncate()
    db.contains_edges.truncate()
