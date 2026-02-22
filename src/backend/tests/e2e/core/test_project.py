import pytest

from app.core.schemas.tree import FolderTreeNode
from app.core.schemas.tree import FileTreeNode


def strip_dynamic_keys(data):
    if isinstance(data, dict):
        for key in ["_key", "_id", "created_at", "updated_at"]:
            data.pop(key, None)

        if "children" in data:
            data["children"] = [strip_dynamic_keys(
                child) for child in data["children"]]
        if "target" in data and data["target"]:
            data["target"] = strip_dynamic_keys(data["target"])

    elif isinstance(data, list):
        return [strip_dynamic_keys(item) for item in data]

    return data


def find_child(node, name):
    """Helper function to find a child node by name."""
    for child in node.get("children", []):
        if child.get("name") == name:
            return child
    return None


@pytest.mark.asyncio
async def test_create_project(client, sample_project_path):
    # Single API call to create the project and get the full tree

    response = await client.post(
        "/api/v1/projects/",
        json={
            "name": "test_project",
            "description": "test_project",
            "path": sample_project_path,
        },
    )
    assert response.status_code == 200
    project_tree = response.json()

    # --- Start Assertions ---

    # The root should have 2 children: main.py and core/
    # Sort children for predictable order

    project_tree["children"].sort(key=lambda x: x["name"])
    assert len(project_tree["children"]) == 2

    core_folder = find_child(project_tree, "core")
    main_py = find_child(project_tree, "main")

    assert core_folder is not None and core_folder["id"].startswith("Folder")
    assert main_py is not None and main_py["id"].startswith("File")

    # 1. Check main.py contents
    assert len(main_py["children"]) == 2

    for child in main_py["children"]:
        assert child["id"].startswith(
            "Function") or child["id"].startswith("Call")

    # 2. Check core/ folder contents
    core_folder["children"].sort(key=lambda x: x["name"])
    assert len(core_folder["children"]) == 2
    model_folder = find_child(core_folder, "model")
    utils_folder = find_child(core_folder, "utils")
    assert model_folder is not None
    assert utils_folder is not None

    # 2a. Check model/ folder contents
    model_folder["children"].sort(key=lambda x: x["name"])
    assert len(model_folder["children"]) == 2
    child_py = find_child(model_folder, "child")
    parent_py = find_child(model_folder, "parent")
    assert child_py is not None
    assert parent_py is not None

    # 2a-i. Check parent.py contents
    assert len(parent_py["children"]) == 1
    parent_class = parent_py["children"][0]
    assert parent_class["name"] == "Parent"

    parent_class["children"].sort(key=lambda x: x["name"])
    assert len(parent_class["children"]) == 2
    parent_init = find_child(parent_class, '__init__')
    parent_get_name = find_child(parent_class, "get_name")
    assert parent_init is not None
    # assert parent_init['node_type'] == 'function'
    assert parent_get_name is not None

    # 2a-ii. Check child.py contents
    assert len(child_py["children"]) == 1
    child_class = child_py["children"][0]
    assert child_class["name"] == "Child"

    assert len(child_class["children"]) == 1
    child_init = find_child(child_class, "__init__")
    assert child_init is not None

    # 2b. Check utils/ folder contents
    assert len(utils_folder["children"]) == 1
    helper_py = utils_folder["children"][0]
    assert helper_py["name"] == "helper"

    # 2b-i. Check helper.py contents
    assert len(helper_py["children"]) == 1
    create_child_func = helper_py["children"][0]
    assert create_child_func["name"] == "create_child"

    assert len(create_child_func["children"]) == 1


@pytest.mark.asyncio
async def test_get_project(client, sample_project_node):
    response = await client.get(f"/api/v1/projects/{sample_project_node.key}")
    assert response.status_code == 200
    project_tree = response.json()
    assert project_tree["name"] == sample_project_node.name
    assert project_tree["description"] == sample_project_node.description
    assert project_tree["path"] == sample_project_node.path


@pytest.mark.asyncio
async def test_update_project(client, sample_project_node):
    response = await client.put(
        f"/api/v1/projects/{sample_project_node.key}",
        json={
            "name": "test_project_updated",
        },
    )
    assert response.status_code == 200
    project_tree = response.json()
    assert project_tree["name"] == "test_project_updated"
    assert project_tree["description"] == sample_project_node.description


@pytest.mark.asyncio
async def test_delete_project(client, sample_project_path, create_repos):
    # 1. Create a project to ensure it has children to be deleted
    response = await client.post(
        "/api/v1/projects/",
        json={
            "name": "sample_project",
            "description": "A project to test deletion",
            "path": sample_project_path,
        },
    )
    assert response.status_code == 200
    project_data = response.json()
    project_key = project_data["_key"]

    # 2. Verify that some child files exist in the database
    file_repo = create_repos.file_repo
    main_py_node = await file_repo.find_by_qname("sample_project.main")
    child_py_node = await file_repo.find_by_qname("sample_project.core.model.child")

    assert main_py_node is not None
    assert child_py_node is not None

    # 3. Delete the project
    response = await client.delete(f"/api/v1/projects/{project_key}")
    assert response.status_code == 204

    # 4. Verify the project is gone
    response = await client.get(f"/api/v1/projects/{project_key}")
    assert response.status_code == 404

    # 5. Verify that the child files are also gone from the database
    main_py_node_after_delete = await file_repo.find_by_qname("sample_project.main")
    child_py_node_after_delete = await file_repo.find_by_qname(
        "sample_project.core.model.child"
    )

    assert main_py_node_after_delete is None
    assert child_py_node_after_delete is None


@pytest.mark.asyncio
async def test_get_all_projects(client, sample_project_node):
    response = await client.get("/api/v1/projects/")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == sample_project_node.name
    assert response.json()[0]["description"] == sample_project_node.description
    assert response.json()[0]["path"] == sample_project_node.path


@pytest.mark.asyncio
async def test_get_project_children(client, sample_project_path):
    # Single API call to create the project and get the full tree
    response = await client.post(
        "/api/v1/projects/",
        json={
            "name": "test_project",
            "description": "test_project",
            "path": sample_project_path,
        },
    )
    assert response.status_code == 200
    key = response.json()["_key"]

    response = await client.get(f"/api/v1/projects/{key}/children")
    assert response.status_code == 200
    assert len(response.json()) == 2

    assert response.json()[1]["name"] == "main"
    assert response.json()[0]["name"] == "core"


@pytest.mark.asyncio
async def test_get_code_from_file(client, sample_project_node):
    print(sample_project_node)
    # response = await client.get(
    #     f'/api/v1/code-elements/{sample_project_node._key}/main.py')
