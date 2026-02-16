import pytest
import shutil
from typing import List

from app.core.builder.tree_builder import TreeBuilder
from app.core.parser.graph_builder.orchestrator import GraphBuilderOrchestrator
from app.core.schemas.tree import AnyTreeNode
from app.core.services.project_service import ProjectService

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


async def _resync_and_get_tree(project_node, repos, db_client):
    """Helper function to resync project and get tree structure."""
    orchestrator = GraphBuilderOrchestrator(
        project_node,
        db=db_client,
        ignore_file_name="v-noc.toml",
    )
    await orchestrator.resync()

    project_service = ProjectService(repos)

    children = await project_service.get_children(project_node.db_name)
    tree_builder = TreeBuilder(children)
    return tree_builder.build()


@pytest.mark.asyncio
async def test_folder_add(setup_folder_project):
    project_node, repos, db_client, project_path = setup_folder_project

    # Build initial tree
    tree_before = await _build_and_get_tree(project_node, repos, db_client)
    assert tree_before, "No tree nodes built"

    # Add new folder
    new_folder = project_path / "new_folder"
    new_folder.mkdir()
    (new_folder / "dummy.py").write_text("")

    # Resync and get updated tree
    tree_after = await _resync_and_get_tree(project_node, repos, db_client)

    # Check tree structure
    project_name = project_node.name
    new_folder_node = find_node_by_qname(
        tree_after, f"{project_name}.new_folder")
    assert new_folder_node is not None, "new_folder not found in tree after add"
    assert new_folder_node.__class__.__name__ == "FolderTreeNode", "new_folder should be a folder"

    # Verify it's in root children
    child_names = [getattr(c, "name", None) for c in tree_after]

    assert "new_folder" in child_names, "new_folder should be in root children"


@pytest.mark.asyncio
async def test_folder_remove(setup_folder_project):
    project_node, repos, db_client, project_path = setup_folder_project

    # Build initial tree
    tree_before = await _build_and_get_tree(project_node, repos, db_client)
    assert tree_before, "No tree nodes built"

    project_name = project_node.name

    # Verify folder exists before removal
    folder1_before = find_node_by_qname(tree_before, f"{project_name}.folder1")
    assert folder1_before is not None, "folder1 should exist before removal"

    # Remove folder
    target = project_path / "folder1"
    shutil.rmtree(target)

    # Resync and get updated tree
    tree_after = await _resync_and_get_tree(project_node, repos, db_client)

    # Check tree structure
    folder1_after = find_node_by_qname(tree_after, f"{project_name}.folder1")
    assert folder1_after is None, "folder1 should not exist in tree after removal"

    # Verify it's not in root children
    child_names = [getattr(c, "name", None) for c in tree_after]
    assert "folder1" not in child_names, "folder1 should not be in root children"


@pytest.mark.asyncio
async def test_folder_move(setup_folder_project):
    project_node, repos, db_client, project_path = setup_folder_project

    # Build initial tree
    tree_before = await _build_and_get_tree(project_node, repos, db_client)
    assert tree_before, "No tree nodes built"

    project_name = project_node.name

    # Create nested structure for move test
    folder1_nested = project_path / "folder1" / "nested1"
    folder2 = project_path / "folder2"
    folder2.mkdir(exist_ok=True)

    # Move "folder1/nested1" to "folder2/nested1"
    src = folder1_nested
    dst = folder2 / "nested1"

    # Verify source exists before move
    nested_before = find_node_by_qname(
        tree_before, f"{project_name}.folder1.nested1")
    assert nested_before is not None, "nested1 should exist before move"

    shutil.move(src, dst)

    # Resync and get updated tree
    tree_after = await _resync_and_get_tree(project_node, repos, db_client)

    # Check tree structure - old location should not exist
    nested_old = find_node_by_qname(
        tree_after, f"{project_name}.folder1.nested1")
    assert nested_old is None, "nested1 should not exist in old location"

    # Check tree structure - new location should exist
    nested_new = find_node_by_qname(
        tree_after, f"{project_name}.folder2.nested1")
    assert nested_new is not None, "nested1 should exist in new location"
    assert nested_new.__class__.__name__ == "FolderTreeNode", "nested1 should be a folder"

    # Verify parent relationships
    folder2_node = find_node_by_qname(tree_after, f"{project_name}.folder2")
    assert folder2_node is not None
    folder2_children = folder2_node.children if hasattr(
        folder2_node, "children") else []
    print("folder2_children --- \n\n", folder2_node)
    child_names = {getattr(c, "name", None) for c in folder2_children}
    assert "nested1" in child_names, "nested1 should be in folder2 children"


@pytest.mark.asyncio
async def test_folder_rename(setup_folder_project):
    project_node, repos, db_client, project_path = setup_folder_project

    # Build initial tree
    tree_before = await _build_and_get_tree(project_node, repos, db_client)
    assert tree_before, "No tree nodes built"

    project_name = project_node.name

    # Rename "folder1" -> "renamed_folder"
    src = project_path / "folder1"
    dst = project_path / "renamed_folder"

    # Verify folder exists before rename
    folder1_before = find_node_by_qname(tree_before, f"{project_name}.folder1")
    assert folder1_before is not None, "folder1 should exist before rename"

    shutil.move(src, dst)

    # Resync and get updated tree
    tree_after = await _resync_and_get_tree(project_node, repos, db_client)

    # Check tree structure - old name should not exist
    folder1_after = find_node_by_qname(tree_after, f"{project_name}.folder1")
    assert folder1_after is None, "folder1 should not exist after rename"

    # Check tree structure - new name should exist
    renamed_folder = find_node_by_qname(
        tree_after, f"{project_name}.renamed_folder")
    assert renamed_folder is not None, "renamed_folder should exist after rename"
    assert renamed_folder.__class__.__name__ == "FolderTreeNode", "renamed_folder should be a folder"

    # Verify it's in root children with new name

    child_names = [getattr(c, "name", None) for c in tree_after]
    assert "renamed_folder" in child_names, "renamed_folder should be in root children"
    assert "folder1" not in child_names, "folder1 should not be in root children"


@pytest.mark.asyncio
async def test_folder_rename_and_move(setup_folder_project):
    project_node, repos, db_client, project_path = setup_folder_project

    # Build initial tree
    tree_before = await _build_and_get_tree(project_node, repos, db_client)
    assert tree_before, "No tree nodes built"

    project_name = project_node.name

    # Create nested structure for rename and move test
    folder1_nested = project_path / "folder1" / "nested1"
    folder2 = project_path / "folder2"
    folder2.mkdir(exist_ok=True)

    # Move "folder1/nested1" -> "folder2/renamed_nested"
    src = folder1_nested
    dst = folder2 / "renamed_nested"

    # Verify source exists before move
    nested_before = find_node_by_qname(
        tree_before, f"{project_name}.folder1.nested1")
    assert nested_before is not None, "nested1 should exist before move"

    shutil.move(src, dst)

    # Resync and get updated tree
    tree_after = await _resync_and_get_tree(project_node, repos, db_client)

    # Check tree structure - old location should not exist
    nested_old = find_node_by_qname(
        tree_after, f"{project_name}.folder1.nested1")
    assert nested_old is None, "nested1 should not exist in old location"

    # Check tree structure - new location with new name should exist
    renamed_nested = find_node_by_qname(
        tree_after, f"{project_name}.folder2.renamed_nested")
    assert renamed_nested is not None, "renamed_nested should exist in new location"
    assert renamed_nested.__class__.__name__ == "FolderTreeNode", "renamed_nested should be a folder"

    # Verify parent relationships
    folder2_node = find_node_by_qname(tree_after, f"{project_name}.folder2")
    assert folder2_node is not None
    folder2_children = folder2_node.children if hasattr(
        folder2_node, "children") else []
    child_names = [getattr(c, "name", None) for c in folder2_children]
    assert "renamed_nested" in child_names, "renamed_nested should be in folder2 children"

    # Verify it's not in old parent
    folder1_node = find_node_by_qname(tree_after, f"{project_name}.folder1")
    if folder1_node:
        folder1_children = folder1_node.children if hasattr(
            folder1_node, "children") else []
        folder1_child_names = [getattr(c, "name", None)
                               for c in folder1_children]
        assert "nested1" not in folder1_child_names, "nested1 should not be in folder1 children"
