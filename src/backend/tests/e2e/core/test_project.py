import json
from pathlib import Path


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
    for child in node.get('children', []):
        if child.get('name') == name:
            return child
    return None


def test_create_project(client, sample_project_path):
    # Single API call to create the project and get the full tree
    response = client.post("/api/v1/projects", json={
        "name": "test_project",
        "description": "test_project",
        "path": sample_project_path
    })
    assert response.status_code == 200
    project_tree = response.json()

    # --- Start Assertions ---

    # The root should have 2 children: main.py and core/
    # Sort children for predictable order
    project_tree['children'].sort(key=lambda x: x['name'])
    assert len(project_tree['children']) == 2

    core_folder = find_child(project_tree, 'core')
    main_py = find_child(project_tree, 'main.py')

    assert core_folder is not None and core_folder['node_type'] == 'folder'
    assert main_py is not None and main_py['node_type'] == 'file'

    # 1. Check main.py contents
    main_py['children'].sort(key=lambda x: x['qname'])
    assert len(main_py['children']) == 2
    main_func = main_py['children'][0]
    main_call = main_py['children'][1]
    assert main_func['name'] == 'main' and main_func['node_type'] == 'function'
    assert main_call['name'] == 'main' and main_call['node_type'] == 'call'

    # 2. Check core/ folder contents
    core_folder['children'].sort(key=lambda x: x['name'])
    assert len(core_folder['children']) == 2
    model_folder = find_child(core_folder, 'model')
    utils_folder = find_child(core_folder, 'utils')
    assert model_folder is not None
    assert utils_folder is not None

    # 2a. Check model/ folder contents
    model_folder['children'].sort(key=lambda x: x['name'])
    assert len(model_folder['children']) == 2
    child_py = find_child(model_folder, 'child.py')
    parent_py = find_child(model_folder, 'parent.py')
    assert child_py is not None
    assert parent_py is not None

    # 2a-i. Check parent.py contents
    assert len(parent_py['children']) == 1
    parent_class = parent_py['children'][0]
    assert parent_class['name'] == 'Parent' and parent_class['node_type'] == 'class'
    parent_class['children'].sort(key=lambda x: x['name'])
    assert len(parent_class['children']) == 2
    parent_init = find_child(parent_class, '__init__')
    parent_get_name = find_child(parent_class, 'get_name')
    assert parent_init is not None and parent_init['node_type'] == 'function'
    assert parent_get_name is not None and parent_get_name['node_type'] == 'function'

    # 2a-ii. Check child.py contents
    assert len(child_py['children']) == 1
    child_class = child_py['children'][0]
    assert child_class['name'] == 'Child' and child_class['node_type'] == 'class'
    assert len(child_class['children']) == 1
    child_init = find_child(child_class, '__init__')
    assert child_init is not None and child_init['node_type'] == 'function'

    # 2b. Check utils/ folder contents
    assert len(utils_folder['children']) == 1
    helper_py = utils_folder['children'][0]
    assert helper_py['name'] == 'helper.py'

    # 2b-i. Check helper.py contents
    assert len(helper_py['children']) == 1
    create_child_func = helper_py['children'][0]
    assert create_child_func['name'] == 'create_child' and create_child_func['node_type'] == 'function'
    assert len(create_child_func['children']) == 1
    init_call = create_child_func['children'][0]
    assert init_call['name'] == '__init__' and init_call['node_type'] == 'call'


def test_get_project(client, sample_project_node):
    response = client.get(f"/api/v1/projects/{sample_project_node.key}")
    assert response.status_code == 200
    project_tree = response.json()
    assert project_tree['name'] == sample_project_node.name
    assert project_tree['description'] == sample_project_node.description
    assert project_tree['path'] == sample_project_node.path


def test_update_project(client, sample_project_node):
    response = client.put(f"/api/v1/projects/{sample_project_node.key}", json={
        "name": "test_project_updated",

    })
    assert response.status_code == 200
    project_tree = response.json()
    assert project_tree['name'] == "test_project_updated"
    assert project_tree['description'] == sample_project_node.description


def test_delete_project(client, sample_project_node):
    response = client.delete(f"/api/v1/projects/{sample_project_node.key}")
    assert response.status_code == 200
    assert response.json() == True

    # response = client.get(f"/api/v1/projects/{sample_project_node.key}")
    # assert response.status_code == 404
