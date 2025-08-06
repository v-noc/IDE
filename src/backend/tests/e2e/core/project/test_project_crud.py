from fastapi.testclient import TestClient
import os
from app.core.manager import CodeGraphManager


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
        "/api/v1/project/",
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

    response = client.get(f"/api/v1/project/{project.key}")

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

    response = client.get("/api/v1/project/")

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
        f"/api/v1/project/{project.key}",
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

    response = client.delete(f"/api/v1/project/{project.key}")

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
    response = client.post("/api/v1/project/", json=payload)
    assert response.status_code == 201
    project_data = response.json()
    project_key = project_data["key"]

    # Retrieve the project tree
    response = client.get(f"/api/v1/project/{project_key}/tree")
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
        (child for child in tree_data["children"] if child["name"] == "models"),
        None
    )
    assert models_folder is not None
    assert models_folder["node_type"] == "folder"

    model_children_names = [
        child["name"] for child in models_folder["children"]
    ]
    assert "user.py" in model_children_names

    # Clean up
    manager.delete_project(project_key)
