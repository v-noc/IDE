import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.manager import CodeGraphManager


@pytest.fixture(scope="module")
def client():
    """
    Yield a TestClient instance for the API.
    """
    with TestClient(app) as c:
        yield c


def test_create_project(client: TestClient, manager: CodeGraphManager):
    """
    Test creating a new project.
    """
    project_name = "Test Project"
    project_path = "/tmp/test_project"
    
    response = client.post(
        "v1/api/project",
        json={"name": project_name, "path": project_path}
    )
    print(response.json())
    assert response.status_code == 201
    data = response.json()
  
    assert data["name"] == project_name
    assert data["path"] == project_path
    assert "key" in data
    
    # Verify the project was actually created
    project_key = data["key"]
    assert manager.get_project(project_key) is not None
    
    # Clean up
    manager.delete_project(project_key)


def test_get_project(client: TestClient, manager: CodeGraphManager):
    """
    Test retrieving a single project.
    """
    # First, create a project to retrieve
    project = manager.create_project(
        name="Test Get Project", path="/tmp/get_project"
    )
    
    response = client.get(f"v1/api/project/{project.key}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Get Project"
    assert data["path"] == "/tmp/get_project"
    assert data["key"] == project.key
    
    # Clean up
    manager.delete_project(project.key)


def test_get_project_not_found(client: TestClient):
    """
    Test retrieving a non-existent project.
    """
    response = client.get("v1/api/project/non_existent_key")
    assert response.status_code == 404


def test_get_all_projects(client: TestClient, manager: CodeGraphManager):
    """
    Test retrieving all projects.
    """
    # Create a couple of projects
    p1 = manager.create_project(name="Project 1", path="/tmp/p1")
    p2 = manager.create_project(name="Project 2", path="/tmp/p2")
    
    response = client.get("v1/api/projects")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    
    project_keys = {p["key"] for p in data}
    assert p1.key in project_keys
    assert p2.key in project_keys
    
    # Clean up
    manager.delete_project(p1.key)
    manager.delete_project(p2.key)


def test_update_project(client: TestClient, manager: CodeGraphManager):
    """
    Test updating a project.
    """
    # Create a project to update
    project = manager.create_project(
        name="Original Name", path="/tmp/original_path"
    )
    
    update_data = {"name": "Updated Name", "path": "/tmp/updated_path"}
    response = client.put(
        f"v1/api/project/{project.key}",
        json=update_data
    )
    print(response.json())
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["path"] == "/tmp/updated_path"
    
    # Verify the update in the manager
    updated_project = manager.get_project(project.key)
    assert updated_project.name == "Updated Name"
    assert updated_project.path == "/tmp/updated_path"
    
    # Clean up
    manager.delete_project(project.key)


def test_delete_project(client: TestClient, manager: CodeGraphManager):
    """
    Test deleting a project.
    """
    # Create a project to delete
    project = manager.create_project(
        name="To Be Deleted", path="/tmp/to_be_deleted"
    )
    
    response = client.delete(f"v1/api/project/{project.key}")
    
    assert response.status_code == 204
    
    # Verify the project is gone
    assert manager.get_project(project.key) is None
