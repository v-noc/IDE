from fastapi.testclient import TestClient
import os
from app.core.manager import CodeGraphManager
from app.db import collections


def test_create_project(
    client: TestClient,
    manager: CodeGraphManager,
    tmp_path
):
    """
    Test creating a new project.
    """
    project_name = "Test Project"
    # Use a temporary path for the project
    project_path = str(tmp_path)
    os.makedirs(project_path, exist_ok=True)

    response = client.post(
        "/api/v1/projects/",
        json={"name": project_name, "path": project_path}
    )
    assert response.status_code == 201
    data = response.json()

    assert data["name"] == project_name
    assert data["path"] == project_path
    assert "key" in data

    # Verify the project was actually created
    project_key = data["key"]
    # We need to scan the project to populate the database
    created_project = manager.get_project(project_key)
    assert created_project is not None

    # Clean up
    manager.delete_project(project_key)


def test_get_project(
    client: TestClient,
    manager: CodeGraphManager,
    tmp_path
):
    """
    Test retrieving a single project.
    """
    project_path = tmp_path / "get_project"
    project_path.mkdir()
    # First, create a project to retrieve
    project = manager.create_project(
        name="Test Get Project", path=str(project_path)
    )

    response = client.get(f"/api/v1/projects/{project.key}")

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Get Project"
    assert data["path"] == str(project_path)
    assert data["key"] == project.key

    # Clean up
    manager.delete_project(project.key)


def test_get_project_not_found(client: TestClient):
    """
    Test retrieving a non-existent project.
    """
    response = client.get("/api/v1/project/non_existent_key")
    assert response.status_code == 404


def test_get_all_projects(
    client: TestClient,
    manager: CodeGraphManager,
    tmp_path
):
    """
    Test retrieving all projects.
    """
    # Create a couple of projects
    p1_path = tmp_path / "p1"
    p1_path.mkdir()
    p2_path = tmp_path / "p2"
    p2_path.mkdir()

    p1 = manager.create_project(name="Project 1", path=str(p1_path))
    p2 = manager.create_project(name="Project 2", path=str(p2_path))

    response = client.get("/api/v1/projects/")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

    project_keys = {p["key"] for p in data}
    assert p1.key in project_keys
    assert p2.key in project_keys

    # Clean up
    manager.delete_project(p1.key)
    manager.delete_project(p2.key)


def test_update_project(
    client: TestClient,
    manager: CodeGraphManager,
    tmp_path
):
    """
    Test updating a project.
    """
    # Create a project to update
    original_path = tmp_path / "original_path"
    original_path.mkdir()
    project = manager.create_project(
        name="Original Name", path=str(original_path)
    )

    updated_path = tmp_path / "updated_path"
    updated_path.mkdir()
    update_data = {"name": "Updated Name", "path": str(updated_path)}
    response = client.put(
        f"/api/v1/projects/{project.key}",
        json=update_data
    )
    print(response.json())
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["path"] == str(updated_path)

    # Verify the update in the manager
    updated_project = manager.get_project(project.key)
    assert updated_project.name == "Updated Name"
    assert updated_project.path == str(updated_path)

    # Clean up
    manager.delete_project(project.key)


def test_delete_project(
    client: TestClient,
    manager: CodeGraphManager,
    tmp_path
):
    """
    Test deleting a project.
    """
    # Create a project to delete
    delete_path = tmp_path / "to_be_deleted"
    delete_path.mkdir()
    project = manager.create_project(
        name="To Be Deleted", path=str(delete_path)
    )

    response = client.delete(f"/api/v1/projects/{project.key}")

    assert response.status_code == 204

    # Verify the project is gone
    assert manager.get_project(project.key) is None


def test_get_project_tree(
    client: TestClient,
    manager: CodeGraphManager,
    sample_project_path: str
):
    """
    Test retrieving project tree structure.
    """
    # Create a project from the sample project path
    project_name = "Sample Project Tree"
    payload = {"name": project_name, "path": sample_project_path}
    response = client.post("/api/v1/projects/", json=payload)
    assert response.status_code == 201
    project_data = response.json()
    project_key = project_data["key"]

    # Retrieve the project tree
    response = client.get(f"/api/v1/projects/{project_key}/tree")
    assert response.status_code == 200
    tree_data = response.json()

    # Assertions on the tree structure
    assert tree_data["name"] == project_name
    assert tree_data["node_type"] == "project"
    assert "children" in tree_data
    assert len(tree_data["children"]) > 0

    # Example: Check for a specific file or folder in the tree
    # This depends on the structure of your sample_project
    children_names = [child["name"] for child in tree_data["children"]]
    assert "main.py" in children_names
    assert "models" in children_names

    models_folder = next(
        (
            child
            for child in tree_data["children"]
            if child["name"] == "models"
        ),
        None,
    )
    assert models_folder is not None
    assert models_folder["node_type"] == "folder"

    model_children_names = [
        child["name"] for child in models_folder["children"]
    ]
    assert "user.py" in model_children_names

    # Clean up
    manager.delete_project(project_key)


def test_update_project_theme_and_icon(
    client: TestClient,
    manager: CodeGraphManager,
    tmp_path,
):
    project = manager.create_project(
        name="Proj Theming",
        path=str(tmp_path),
    )

    theme = {
        "navbarColor": "#111111",
        "leftSidebarColor": "#222222",
        "rightSidebarColor": "#333333",
        "backgroundColor": "#444444",
        "textColor": "#555555",
        "iconColor": "#666666",
        "cardColor": "#777777",
    }

    theme_url = f"/api/v1/core/{project.key}/update-node-theme"
    r1 = client.post(theme_url, json=theme)
    assert r1.status_code == 200, r1.text
    themed = r1.json()
    assert themed["properties"]["metaData"]["navbarColor"] == "#111111"

    icon_url = f"/api/v1/core/{project.key}/update-icon"
    r2 = client.post(icon_url, json={"icon": "project-rocket"})
    assert r2.status_code == 200, r2.text
    updated = r2.json()
    assert updated["icon"] == "project-rocket"


def test_update_folder_theme_and_icon(
    client: TestClient,
    manager: CodeGraphManager,
    tmp_path,
):
    project = manager.create_project(
        name="Folder Theming",
        path=str(tmp_path),
    )
    folder = project.add_folder(
        folder_name="src",
        folder_path=str(tmp_path / "src"),
    )

    theme = {
        "navbarColor": "#AAAAAA",
        "leftSidebarColor": "#BBBBBB",
        "rightSidebarColor": "#CCCCCC",
        "backgroundColor": "#DDDDDD",
        "textColor": "#EEEEEE",
        "iconColor": "#999999",
        "cardColor": "#888888",
    }

    r1 = client.post(
        f"/api/v1/core/{folder.key}/update-node-theme",
        json=theme,
    )
    assert r1.status_code == 200, r1.text
    themed = r1.json()
    assert themed["properties"]["metaData"]["leftSidebarColor"] == "#BBBBBB"

    r2 = client.post(
        f"/api/v1/core/{folder.key}/update-icon",
        json={"icon": "folder-star"},
    )
    assert r2.status_code == 200, r2.text
    updated = r2.json()
    assert updated["icon"] == "folder-star"


def test_update_file_theme_and_icon(
    client: TestClient,
    manager: CodeGraphManager,
    tmp_path,
):
    project = manager.create_project(
        name="File Theming",
        path=str(tmp_path),
    )
    file_node = project.add_file(
        file_name="main.py",
        file_path=str(tmp_path / "main.py"),
    )

    theme = {
        "navbarColor": "#010101",
        "leftSidebarColor": "#020202",
        "rightSidebarColor": "#030303",
        "backgroundColor": "#040404",
        "textColor": "#050505",
        "iconColor": "#060606",
        "cardColor": "#070707",
    }

    r1 = client.post(
        f"/api/v1/core/{file_node.key}/update-node-theme",
        json=theme,
    )
    assert r1.status_code == 200, r1.text
    themed = r1.json()
    assert themed["properties"]["metaData"]["rightSidebarColor"] == "#030303"

    r2 = client.post(
        f"/api/v1/core/{file_node.key}/update-icon",
        json={"icon": "file-code"},
    )
    assert r2.status_code == 200, r2.text
    updated = r2.json()
    assert updated["icon"] == "file-code"


def test_update_function_and_class_theme_and_icon(
    client: TestClient,
    manager: CodeGraphManager,
    sample_project_path: str,
):
    from app.core.parser.project_scanner import ProjectScanner

    scanner = ProjectScanner(sample_project_path)
    scanner.scan()

    # Function node (use known sample function qname if present, otherwise any)
    func_node = collections.nodes.find_one({
        "qname": "main.start_app"
    }) or collections.nodes.find_one({"node_type": "function"})
    assert func_node, "No function node found after scanning"

    klass_node = collections.nodes.find_one({"node_type": "class"})
    assert klass_node, "No class node found after scanning"

    theme = {
        "navbarColor": "#111111",
        "leftSidebarColor": "#121212",
        "rightSidebarColor": "#131313",
        "backgroundColor": "#141414",
        "textColor": "#151515",
        "iconColor": "#161616",
        "cardColor": "#171717",
    }

    # Update function
    r1 = client.post(
        f"/api/v1/core/{func_node.key}/update-node-theme",
        json=theme,
    )
    assert r1.status_code == 200, r1.text
    themed_func = r1.json()
    assert themed_func["properties"]["metaData"]["textColor"] == "#151515"
    r2 = client.post(
        f"/api/v1/core/{func_node.key}/update-icon",
        json={"icon": "function-bolt"},
    )
    assert r2.status_code == 200, r2.text
    assert r2.json()["icon"] == "function-bolt"

    # Update class
    r3 = client.post(
        f"/api/v1/core/{klass_node.key}/update-node-theme",
        json=theme,
    )
    assert r3.status_code == 200, r3.text
    themed_class = r3.json()
    assert themed_class["properties"]["metaData"]["iconColor"] == "#161616"
    r4 = client.post(
        f"/api/v1/core/{klass_node.key}/update-icon",
        json={"icon": "class-cube"},
    )
    assert r4.status_code == 200, r4.text
    assert r4.json()["icon"] == "class-cube"
