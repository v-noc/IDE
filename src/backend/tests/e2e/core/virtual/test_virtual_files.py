from fastapi.testclient import TestClient
from app.core.manager import CodeGraphManager


def test_create_virtual_file(client: TestClient, manager: CodeGraphManager):
    project = manager.create_project(
        name="Test Create Project", path="/tmp/create_project"
    )

    folder = project.add_virtual_folder(folder_name="Test Virtual Folder")
    # folder.add_virtual_file(file_name="Test Virtual File", description="Test Description")

    response = client.post(
        f"v1/api/virtual-file",
        json={
            "project_id": project.key,
            "name": "Test Virtual File",
            "description": "Test Description",
            "parent_id": folder.key
        }
    )

    data = response.json()
    assert response.status_code == 201
    assert data["name"] == "Test Virtual File"
    assert data["description"] == "Test Description"
    assert data["qname"] == f"{project.qname}.Test Virtual Folder.Test Virtual File"
 
    assert data["node_type"] == "virtual_file"

def test_get_virtual_file(client: TestClient, manager: CodeGraphManager):
    project = manager.create_project(
        name="Test Get Project", path="/tmp/get_project"
    )

    folder = project.add_virtual_folder(folder_name="Test Virtual Folder")
    file = folder.add_virtual_file(file_name="Test Virtual File", description="Test Description")

    response = client.get(
        f"v1/api/virtual-file/{file.key}"
    )
    data = response.json()
    assert response.status_code == 200
    assert data["name"] == "Test Virtual File"
    assert data["description"] == "Test Description"
    assert data["qname"] == f"{project.qname}.Test Virtual Folder.Test Virtual File"
    assert data["node_type"] == "virtual_file"


def test_update_virtual_file(client: TestClient, manager: CodeGraphManager):
    project = manager.create_project(
        name="Test Update Project", path="/tmp/update_project"
    )

    folder = project.add_virtual_folder(folder_name="Test Virtual Folder")
    file = folder.add_virtual_file(file_name="Test Virtual File", description="Test Description")
    
    response = client.put(
        f"v1/api/virtual-file/{file.key}",
        json={
            "name": "Test Virtual File Updated",
            "description": "Test Description Updated"
        }
    )
    data = response.json()
    assert response.status_code == 200
    assert data["name"] == "Test Virtual File Updated"

    for i in folder.get_virtual_files():
        assert i.name in ["Test Virtual File", "Test Virtual File Updated"]

def test_delete_virtual_file(client: TestClient, manager: CodeGraphManager):
    project = manager.create_project(
        name="Test Delete Project", path="/tmp/delete_project"
    )

    folder = project.add_virtual_folder(folder_name="Test Virtual Folder")
    file = folder.add_virtual_file(file_name="Test Virtual File", description="Test Description")

    response = client.delete(
        f"v1/api/virtual-file/{file.key}"
    )
    assert response.status_code == 204

    assert len(folder.get_virtual_files()) == 0
   