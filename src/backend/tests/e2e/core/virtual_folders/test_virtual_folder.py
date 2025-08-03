from fastapi.testclient import TestClient

from app.core.manager import CodeGraphManager


def test_create_virtual_folder(client: TestClient, manager: CodeGraphManager):
    # First, create a project to retrieve
    project = manager.create_project(
        name="Test Get Project", path="/tmp/get_project"
    )

    response = client.post(
        "v1/api/virtual-folder",
        json={
            "project_id": project.key,
            "name": "Test Virtual Folder",
            "description": "Test Description"
        }
    )
    data = response.json()
    assert response.status_code == 201
    assert data["name"] == "Test Virtual Folder"
    assert data["description"] == "Test Description"
    
   
    assert data["key"] is not None
    assert data["qname"] == f"{project.qname}.Test Virtual Folder"
    assert data["node_type"] == "virtual_folder"

    response = client.post(
        "v1/api/virtual-folder",
        json={
            "project_id": project.key,
            "name": "Test Virtual Folder 2",
            "description": "Test Description 2",
            "parent_id": data["key"]
        }
    )
    data = response.json()
    assert response.status_code == 201
    assert data["name"] == "Test Virtual Folder 2"
    assert data["description"] == "Test Description 2"
    assert data["qname"] == f"{project.qname}.Test Virtual Folder.Test Virtual Folder 2"

def test_get_virtual_folder(client: TestClient, manager: CodeGraphManager):
    project = manager.create_project(
        name="Test Get Project", path="/tmp/get_project"
    )

    project.add_virtual_folder(folder_name="Test Virtual Folder")
    project.add_virtual_folder(folder_name="Test Virtual Folder 2")

    response = client.get(
        f"v1/api/project/{project.key}/virtual-folders"
    )
    data = response.json()
    assert response.status_code == 200
    assert len(data) == 2
    for folder in data:
        assert folder["name"] in ["Test Virtual Folder", "Test Virtual Folder 2"]


