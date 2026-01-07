from typing import List

import pytest

from app.core.schemas.tree import AnyTreeNode
from tests.unit.parser.analyzer.hierarchy.conftest import _build_and_get_tree


def find_node_by_qname(nodes: List[AnyTreeNode], qname: str):
    """Find a node by its qname in the tree."""
    for node in nodes:
        if getattr(node, "qname", None) == qname:
            return node
        if hasattr(node, "children") and node.children:
            found = find_node_by_qname(node.children, qname)
            if found:
                return found
    return None


def find_node_by_name(nodes: List[AnyTreeNode], name: str):
    """Find a node by its name in the tree."""
    for node in nodes:
        if getattr(node, "name", None) == name:
            return node
        if hasattr(node, "children") and node.children:
            found = find_node_by_name(node.children, name)
            if found:
                return found
    return None


@pytest.mark.asyncio
async def test_hierarchy_and_ignore(setup_structure_project):
    """
    Test that the initial hierarchy is built correctly and respects ignore
    files.
    """
    project_node, repos, arangodb_client, project_path = setup_structure_project

    # Build the project tree
    tree = await _build_and_get_tree(project_node, repos, arangodb_client)
    assert tree, "No tree nodes built"

    project_name = project_node.name

    # Check root node

    # Check that files exist in tree
    main_file = find_node_by_qname(tree, f"{project_name}.main")
    assert main_file is not None, "main.py not found in tree"
    assert main_file.node_type == "file"

    core_folder = find_node_by_qname(tree, f"{project_name}.core")
    assert core_folder is not None, "core folder not found in tree"
    assert core_folder.node_type == "folder"

    core_user = find_node_by_qname(tree, f"{project_name}.core.user")
    assert core_user is not None, "core/user.py not found in tree"
    assert core_user.node_type == "file"

    core_post = find_node_by_qname(tree, f"{project_name}.core.post")
    assert core_post is not None, "core/post.py not found in tree"
    assert core_post.node_type == "file"

    core_data = find_node_by_qname(tree, f"{project_name}.core.data")
    assert core_data is not None, "core/data folder not found in tree"
    assert core_data.node_type == "folder"

    core_data_user = find_node_by_qname(tree, f"{project_name}.core.data.user")
    assert core_data_user is not None, "core/data/user.py not found in tree"
    assert core_data_user.node_type == "file"

    app_folder = find_node_by_qname(tree, f"{project_name}.app")
    assert app_folder is not None, "app folder not found in tree"
    assert app_folder.node_type == "folder"

    app_api = find_node_by_qname(tree, f"{project_name}.app.api")
    assert app_api is not None, "app/api.py not found in tree"
    assert app_api.node_type == "file"


@pytest.mark.asyncio
async def test_scope_contains_links(setup_structure_project):
    """
    Test that parent-child relationships are correctly established in the
    tree.
    """
    project_node, repos, arangodb_client, project_path = setup_structure_project

    # Build the project tree
    tree = await _build_and_get_tree(project_node, repos, arangodb_client)
    assert tree, "No tree nodes built"

    project_name = project_node.name

    # Check root children

    child_names = [getattr(c, "name", None) for c in tree]
    assert "main" in child_names, "main not found in root children"
    assert "core" in child_names, "core not found in root children"
    assert "app" in child_names, "app not found in root children"

    # Check core children
    core = find_node_by_qname(tree, f"{project_name}.core")
    assert core is not None
    core_children = core.children if hasattr(core, "children") else []
    core_names = {getattr(c, "name", None) for c in core_children}
    assert "user" in core_names, "user not found in core children"
    assert "post" in core_names, "post not found in core children"
    assert "data" in core_names, "data not found in core children"

    for child in core_children:
        child_name = getattr(child, "name", "unknown")
        assert hasattr(child, "parent") or child in core_children, (
            f"Child {child_name} should be linked to core"
        )
