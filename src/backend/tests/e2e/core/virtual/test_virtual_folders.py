from fastapi.testclient import TestClient
from app.core.manager import CodeGraphManager
import pytest

pytestmark = pytest.mark.usefixtures("clean_collections")


def test_create_virtual_folder(client: TestClient, manager: CodeGraphManager):
    """
    Tests creating a virtual folder at the project root and as a child
    of another virtual folder.
    """
    project = manager.create_project(
        name="Test Project", path="/tmp/test_project"
    )

    # Create root virtual folder
    response = client.post(
        f"/api/v1/{project.key}/virtual-folder",
        json={
            "name": "root_folder",
            "description": "This is a root folder."
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data['name'] == 'root_folder'
    assert data['qname'] == f'{project.qname}.root_folder'
    root_folder_key = data['key']

    # Create child virtual folder
    response = client.post(
        f"/api/v1/{project.key}/virtual-folder",
        json={
            "name": "child_folder",
            "description": "This is a child folder.",
            "parent_id": root_folder_key
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data['name'] == 'child_folder'
    assert data['qname'] == f'{project.qname}.root_folder.child_folder'


def test_update_virtual_folder(client: TestClient, manager: CodeGraphManager):
    """
    Tests updating a virtual folder's name and description.
    """
    project = manager.create_project(
        name="Test Project", path="/tmp/test_project"
    )
    folder = project.add_virtual_folder(folder_name="original_name")

    response = client.put(
        f"/api/v1/{project.key}/virtual-folder/{folder.key}",
        json={
            "name": "updated_name",
            "description": "Updated description."
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data['name'] == 'updated_name'
    assert data['description'] == 'Updated description.'


def test_get_virtual_folder_tree(client: TestClient, manager: CodeGraphManager):
    """
    Tests retrieving a virtual folder and its descendant tree.
    """
    project = manager.create_project(
        name="Test Project", path="/tmp/test_project"
    )
    root_folder = project.add_virtual_folder(folder_name="root")
    child1 = root_folder.add_virtual_folder(folder_name="child1")
    root_folder.add_virtual_folder(folder_name="child2")
    child1.add_virtual_folder(folder_name="grandchild")

    url = f"/api/v1/{project.key}/virtual-folder/{root_folder.key}"
    response = client.get(url)
    assert response.status_code == 200
    data = response.json()
    
    assert data['name'] == 'root'
    assert len(data['children']) == 2
    
    child_names = {c['name'] for c in data['children']}
    assert child_names == {'child1', 'child2'}
    
    for child in data['children']:
        if child['name'] == 'child1':
            assert len(child['children']) == 1
            assert child['children'][0]['name'] == 'grandchild'


def test_add_code_element(client: TestClient, manager: CodeGraphManager, sample_project_path):
    """
    Tests adding a code element to a virtual folder and then removing it.
    """
    from app.core.parser.project_scanner import ProjectScanner
    from app.db import collections
    
    scanner = ProjectScanner(sample_project_path)
    scanner.scan()
    project = manager.get_all_projects()[0]
    
    folder = project.add_virtual_folder(folder_name="test_folder")
    
    # Get a code element to add
    function_doc = collections.nodes.find_one({"qname": "main.start_app"})
    assert function_doc, "Function 'main.start_app' not found"
    
    # Add code element
    add_response = client.post(
        f"/api/v1/{project.key}/virtual-folder/{folder.key}/add-code-element",
        json={
            "element_id": function_doc.id,
            "parent_folder_key": folder.key
        }
    )
    assert add_response.status_code == 201
    
    # Verify it was added
    get_response = client.get(f"/api/v1/{project.key}/virtual-folder/{folder.key}")
    data = get_response.json()
    assert len(data['children']) == 1
    assert data['children'][0]['link_to']['qname'] == 'main.start_app'
   

