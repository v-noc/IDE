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


async def get_project_tree(client, project_id):
    """Fetch project tree via API."""
    response = await client.get(f"/api/v1/projects/?project_id={project_id}")
    assert response.status_code == 200
    data = response.json()
    return data.get("children", [])


@pytest.mark.asyncio
async def test_create_structure_group_child_removed_from_previous_parent(client, built_sample_project):
    """
    When creating a structure group, the child should be removed from its previous
    parent and exist in the new group.
    """
    project_node, _ = built_sample_project
    project_id = project_node.id

    # Get initial tree via API
    tree = await get_project_tree(client, project_id)

    # Find main.py (file at root) and core folder
    main_file = find_node_by_name(tree, "main")
    assert main_file is not None, "main.py should exist"

    main_id = main_file["id"]

    # Create structure group via API with main.py as child
    response = await client.post(
        "/api/v1/groups",
        params={
            "project_id": project_id,
            "group_type": "structure_group",
        },
        json={
            "name": "My Group",
            "description": "Group containing main.py",
            "children": [{"id": main_id, "type": "file"}],
        },
    )
    assert response.status_code == 200
    group = response.json()
    group_id = group["id"]

    # Get tree after creation via API
    tree_after = await get_project_tree(client, project_id)

    # Find the group in the tree
    group_node = find_node_by_id(tree_after, group_id)
    assert group_node is not None, "Group should exist in tree"

    # main.py should be IN the group (removed from project root)
    group_child_ids = [c["id"] for c in group_node.get("children", [])]

    assert main_id in group_child_ids, "main.py should be a child of the group"

    # main.py should NOT be a direct child of project anymore
    root_ids = [n["id"] for n in tree_after]
    assert main_id not in root_ids, "main.py should not be at project root (moved to group)"


@pytest.mark.asyncio
async def test_edit_structure_group_add_remove_children(client, built_sample_project):
    """
    Test adding and removing children from a structure group via API.
    """
    project_node, _ = built_sample_project
    project_id = project_node.id

    # Get initial tree via API
    tree = await get_project_tree(client, project_id)

    main_file = find_node_by_name(tree, "main")
    core_folder = find_node_by_name(tree, "core")
    assert main_file and core_folder

    # Create group with main.py only via API
    response = await client.post(
        "/api/v1/groups",
        params={
            "project_id": project_id,

            "group_type": "structure_group",
        },
        json={
            "name": "Edit Test Group",
            "description": "Group for add/remove test",
            "children": [{"id": main_file["id"], "type": "file"}],
        },
    )
    assert response.status_code == 200
    group = response.json()
    group_id = group["id"]

    # Add core folder to the group via API
    response = await client.post(
        "/api/v1/groups/children",
        params={
            "project_id": project_id,
            "group_id": group_id,
            "child_id": core_folder["id"],
            "group_type": "structure_group",
        },
        json={
            "item_type": "folder",
        },
    )
    assert response.status_code == 200

    # Verify group has both children (main + core)
    tree_after_add = await get_project_tree(client, project_id)
    group_node = find_node_by_id(tree_after_add, group_id)
    assert group_node is not None
    assert len(group_node.get("children", [])
               ) == 2, "Group should have main and core"

    # Remove main from group (move back to project) via API
    response = await client.delete(
        "/api/v1/groups/children",
        params={
            "project_id": project_id,
            "group_id": group_id,
            "child_id": main_file["id"],
            "group_type": "structure_group",
            "item_type": "file"
        },
    )
    assert response.status_code == 204

    # Verify group has only core now
    tree_after_remove = await get_project_tree(client, project_id)
    group_node_after = find_node_by_id(tree_after_remove, group_id)
    assert group_node_after is not None
    child_ids = [c["id"] for c in group_node_after.get("children", [])]
    assert core_folder["id"] in child_ids, "core should still be in group"
    assert main_file["id"] not in child_ids, "main should be removed from group"


@pytest.mark.asyncio
async def test_delete_structure_group_children_move_to_parent(client, built_sample_project):
    """
    When a structure group is deleted via API, its children should move to the group's parent.
    """
    project_node, _ = built_sample_project
    project_id = project_node.id

    # Get initial tree via API
    tree = await get_project_tree(client, project_id)

    core_folder = find_node_by_name(tree, "core")
    main_file = find_node_by_name(tree, "main")
    assert core_folder and main_file

    # Create group under core folder with main.py as child via API
    response = await client.post(
        "/api/v1/groups",
        params={
            "project_id": project_id,
            "parent_node_id": core_folder["id"],
            "group_type": "structure_group",
        },
        json={
            "name": "Group To Delete",
            "description": "Group whose children will move to parent on delete",
            "children": [{"id": main_file["id"], "type": "file"}],
        },
    )
    assert response.status_code == 200
    group = response.json()
    group_id = group["id"]

    # Verify group has main
    tree_before = await get_project_tree(client, project_id)
    group_node = find_node_by_id(tree_before, group_id)
    assert group_node is not None
    assert main_file["id"] in [c["id"] for c in group_node.get("children", [])]

    # Delete the group via API
    response = await client.delete(
        "/api/v1/groups",
        params={
            "project_id": project_id,
            "group_id": group_id,
            "group_type": "structure_group",
        },
    )
    assert response.status_code == 204

    # Children should move to group's parent (core folder)
    tree_after = await get_project_tree(client, project_id)

    # Group should be gone
    group_after = find_node_by_id(tree_after, group_id)
    assert group_after is None, "Group should be deleted"

    # main.py should now be under core folder (the group's parent)
    core_after = find_node_by_name(tree_after, "core")
    assert core_after is not None
    core_child_ids = [c["id"] for c in core_after.get("children", [])]
    assert main_file[
        "id"] in core_child_ids, "main.py should have moved to core (group's parent)"
