import pytest


def find_node_by_name(nodes, name):
    """Recursively find a node by name in a list of tree node dicts."""
    for node in nodes:
        if node.get("name") == name:
            return node
        children = node.get("children", [])
        if children:
            found = find_node_by_name(children, name)
            if found:
                return found
    return None


def find_node_by_id(nodes, node_id):
    """Recursively find a node by id in a list of tree node dicts."""
    for node in nodes:
        if node.get("id") == node_id:
            return node
        children = node.get("children", [])
        if children:
            found = find_node_by_id(children, node_id)
            if found:
                return found
    return None


def find_first_child_of_type(node, node_type):
    """Find the first child of a node matching the given node_type."""
    for child in node.get("children", []):
        if child.get("node_type") == node_type:
            return child
    return None


async def get_project_tree(client, project_id):
    """Fetch project tree via API."""
    response = await client.get(f"/api/v1/projects/?project_id={project_id}")
    assert response.status_code == 200
    data = response.json()
    return data.get("children", [])


@pytest.mark.asyncio
async def test_create_code_element_group_child_removed_from_previous_parent(
    client, built_sample_project
):
    """
    When creating a code element group, the child (function/class) should be
    removed from its previous parent (file) and exist in the new group.
    """
    project_node, _ = built_sample_project
    project_id = project_node.id

    tree = await get_project_tree(client, project_id)

    # Find main.py file and its main() function
    main_file = find_node_by_name(tree, "main")
    assert main_file is not None, "main.py should exist"

    main_func = find_first_child_of_type(main_file, "function")
    assert main_func is not None, "main.py should have at least one function"

    main_func_id = main_func["id"]
    main_file_id = main_file["id"]

    # Create code element group via API with main() as child
    response = await client.post(
        "/api/v1/groups",
        params={
            "project_id": project_id,
            "parent_node_id": main_file_id,
            "group_type": "code_element_group",
        },
        json={
            "name": "My Code Group",
            "description": "Group containing main function",
            "children": [{"id": main_func_id, "type": "function"}],
        },
    )
    assert response.status_code == 200
    group = response.json()
    group_id = group["id"]

    # Get tree after creation via API
    tree_after = await get_project_tree(client, project_id)

    # Find the group in the tree
    group_node = find_node_by_id(tree_after, group_id)
    assert group_node is not None, "Group should exist under main file"

    # main() should be IN the group (removed from file's direct children)
    group_child_ids = [c["id"] for c in group_node.get("children", [])]
    assert main_func_id in group_child_ids, "main() should be a child of the group"

    # main() should NOT be a direct child of main file anymore
    main_file_after = find_node_by_name(tree_after, "main")
    file_child_ids = [c["id"] for c in main_file_after.get("children", [])]
    assert main_func_id not in file_child_ids, (
        "main() should not be direct child of file (moved to group)"
    )


@pytest.mark.asyncio
async def test_edit_code_element_group_add_remove_children(
    client, built_sample_project
):
    """
    Test adding and removing children from a code element group via API.
    """
    project_node, _ = built_sample_project
    project_id = project_node.id

    tree = await get_project_tree(client, project_id)

    # Find main.py and core/utils/helper.py (for create_child function)
    main_file = find_node_by_name(tree, "main")
    helper_file = find_node_by_name(tree, "helper")
    assert main_file and helper_file, "main.py and helper.py should exist"

    main_func = find_first_child_of_type(main_file, "function")
    helper_func = find_first_child_of_type(helper_file, "function")
    assert main_func and helper_func

    # Create group with main() only via API
    response = await client.post(
        "/api/v1/groups",
        params={
            "project_id": project_id,
            "parent_node_id": main_file["id"],
            "group_type": "code_element_group",
        },
        json={
            "name": "Edit Test Code Group",
            "description": "Group for add/remove test",
            "children": [{"id": main_func["id"], "type": "function"}],
        },
    )
    assert response.status_code == 200
    group = response.json()
    group_id = group["id"]

    # Add create_child function to the group via API
    response = await client.post(
        "/api/v1/groups/children",
        params={
            "project_id": project_id,
            "group_id": group_id,
            "child_id": helper_func["id"],
            "group_type": "code_element_group",
        },
        json={"item_type": "function"},
    )
    assert response.status_code == 200

    # Verify group has both children (main + create_child)
    tree_after_add = await get_project_tree(client, project_id)
    group_node = find_node_by_id(tree_after_add, group_id)
    assert group_node is not None
    assert len(group_node.get("children", [])) == 2, (
        "Group should have main and create_child"
    )

    # Remove main from group (move back to file) via API
    response = await client.delete(
        "/api/v1/groups/children",
        params={
            "project_id": project_id,
            "group_id": group_id,
            "child_id": main_func["id"],
            "group_type": "code_element_group",
            "item_type": "function",
            "new_parent_id": main_file["id"],
        },
    )
    assert response.status_code == 204

    # Verify group has only create_child now
    tree_after_remove = await get_project_tree(client, project_id)
    group_node_after = find_node_by_id(tree_after_remove, group_id)
    assert group_node_after is not None
    child_ids = [c["id"] for c in group_node_after.get("children", [])]
    assert helper_func["id"] in child_ids, "create_child should still be in group"
    assert main_func["id"] not in child_ids, "main should be removed from group"


@pytest.mark.asyncio
async def test_delete_code_element_group_children_move_to_parent(
    client, built_sample_project
):
    """
    When a code element group is deleted via API, its children should move
    to the group's parent (the file).
    """
    project_node, _ = built_sample_project
    project_id = project_node.id

    tree = await get_project_tree(client, project_id)

    main_file = find_node_by_name(tree, "main")
    main_func = find_first_child_of_type(main_file, "function")
    assert main_file and main_func

    # Create group under main file with main() as child via API
    response = await client.post(
        "/api/v1/groups",
        params={
            "project_id": project_id,
            "parent_node_id": main_file["id"],
            "group_type": "code_element_group",
        },
        json={
            "name": "Group To Delete",
            "description": "Group whose children will move to parent on delete",
            "children": [{"id": main_func["id"], "type": "function"}],
        },
    )
    assert response.status_code == 200
    group = response.json()
    group_id = group["id"]

    # Verify group has main
    tree_before = await get_project_tree(client, project_id)
    group_node = find_node_by_id(tree_before, group_id)
    assert group_node is not None
    assert main_func["id"] in [c["id"] for c in group_node.get("children", [])]

    # Delete the group via API
    response = await client.delete(
        "/api/v1/groups",
        params={
            "project_id": project_id,
            "group_id": group_id,
            "group_type": "code_element_group",
        },
    )
    assert response.status_code == 204

    # Children should move to group's parent (main file)
    tree_after = await get_project_tree(client, project_id)

    # Group should be gone
    group_after = find_node_by_id(tree_after, group_id)
    assert group_after is None, "Group should be deleted"

    # main() should now be direct child of main file again
    main_file_after = find_node_by_name(tree_after, "main")
    file_child_ids = [c["id"] for c in main_file_after.get("children", [])]
    assert main_func["id"] in file_child_ids, (
        "main() should have moved back to main file (group's parent)"
    )
