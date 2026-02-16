import shutil
from typing import List

import pytest

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


async def _resync_and_get_tree(project_node, repos, db):
    """Helper function to resync project and get tree structure."""
    orchestrator = GraphBuilderOrchestrator(
        project_node,
        db=db,
        ignore_file_name="v-noc.toml",
    )
    await orchestrator.resync()

    project_service = ProjectService(repos)

    children = await project_service.get_children(project_node.db_name)
    tree_builder = TreeBuilder(children)
    return tree_builder.build()


@pytest.mark.asyncio
async def test_file_add(setup_file_project):
    project_node, repos, arangodb_client, project_path = setup_file_project

    # Build initial tree
    tree_before = await _build_and_get_tree(project_node, repos, arangodb_client)
    assert tree_before, "No tree nodes built"

    # Add new file
    new_file = project_path / "new_file.py"
    new_file.write_text("# new file")

    # Resync and get updated tree
    tree_after = await _resync_and_get_tree(project_node, repos, arangodb_client)

    # Check tree structure
    project_name = project_node.name
    new_file_node = find_node_by_qname(tree_after, f"{project_name}.new_file")
    assert new_file_node is not None, "new_file not found in tree after add"
    assert new_file_node.__class__.__name__ == "FileTreeNode", "new_file should be a file"

    # Verify it's in root children

    child_names = [getattr(c, "name", None) for c in tree_after]
    assert "new_file" in child_names, "new_file should be in root children"


@pytest.mark.asyncio
async def test_file_remove(setup_file_project):
    project_node, repos, arangodb_client, project_path = setup_file_project

    # Build initial tree
    tree_before = await _build_and_get_tree(project_node, repos, arangodb_client)
    assert tree_before, "No tree nodes built"

    project_name = project_node.name

    # Verify file exists before removal
    file1_before = find_node_by_qname(tree_before, f"{project_name}.file1")
    assert file1_before is not None, "file1 should exist before removal"

    # Remove file
    target = project_path / "file1.py"
    target.unlink()

    # Resync and get updated tree
    tree_after = await _resync_and_get_tree(project_node, repos, arangodb_client)

    # Check tree structure
    file1_after = find_node_by_qname(tree_after, f"{project_name}.file1")
    assert file1_after is None, "file1 should not exist in tree after removal"

    # Verify it's not in root children

    child_names = [getattr(c, "name", None) for c in tree_after]
    assert "file1" not in child_names, "file1 should not be in root children"


@pytest.mark.asyncio
async def test_file_move(setup_file_project):
    project_node, repos, arangodb_client, project_path = setup_file_project

    # Build initial tree
    tree_before = await _build_and_get_tree(project_node, repos, arangodb_client)
    assert tree_before, "No tree nodes built"

    project_name = project_node.name

    # Create a folder to move file into
    target_folder = project_path / "subfolder"
    target_folder.mkdir(exist_ok=True)
    (target_folder / "__init__.py").write_text("")

    # Move "file1.py" -> "subfolder/file1.py"
    src = project_path / "file1.py"
    dst = target_folder / "file1.py"

    # Verify file exists before move
    file1_before = find_node_by_qname(tree_before, f"{project_name}.file1")
    assert file1_before is not None, "file1 should exist before move"

    shutil.move(src, dst)

    # Resync and get updated tree
    tree_after = await _resync_and_get_tree(project_node, repos, arangodb_client)

    # Check tree structure - old location should not exist
    file1_old = find_node_by_qname(tree_after, f"{project_name}.file1")
    assert file1_old is None, "file1 should not exist in old location"

    # Check tree structure - new location should exist
    file1_new = find_node_by_qname(
        tree_after, f"{project_name}.subfolder.file1")
    assert file1_new is not None, "file1 should exist in new location"
    assert file1_new.__class__.__name__ == "FileTreeNode", "file1 should be a file"

    # Verify parent relationships
    subfolder_node = find_node_by_qname(
        tree_after, f"{project_name}.subfolder")
    assert subfolder_node is not None
    subfolder_children = (
        subfolder_node.children if hasattr(subfolder_node, "children") else []
    )
    child_names = [getattr(c, "name", None) for c in subfolder_children]
    assert "file1" in child_names, "file1 should be in subfolder children"


@pytest.mark.asyncio
async def test_file_rename(setup_file_project):
    project_node, repos, arangodb_client, project_path = setup_file_project

    # Build initial tree
    tree_before = await _build_and_get_tree(project_node, repos, arangodb_client)
    assert tree_before, "No tree nodes built"

    project_name = project_node.name

    # Rename "file1.py" -> "renamed_file.py"
    src = project_path / "file1.py"
    dst = project_path / "renamed_file.py"

    # Verify file exists before rename
    file1_before = find_node_by_qname(tree_before, f"{project_name}.file1")
    assert file1_before is not None, "file1 should exist before rename"

    shutil.move(src, dst)

    # Resync and get updated tree
    tree_after = await _resync_and_get_tree(project_node, repos, arangodb_client)

    # Check tree structure - old name should not exist
    file1_after = find_node_by_qname(tree_after, f"{project_name}.file1")
    assert file1_after is None, "file1 should not exist after rename"

    # Check tree structure - new name should exist
    renamed_file = find_node_by_qname(
        tree_after, f"{project_name}.renamed_file")
    assert renamed_file is not None, "renamed_file should exist after rename"
    assert renamed_file.__class__.__name__ == "FileTreeNode", "renamed_file should be a file"

    # Verify it's in root children with new name

    child_names = [getattr(c, "name", None) for c in tree_after]
    assert "renamed_file" in child_names, "renamed_file should be in root children"
    assert "file1" not in child_names, "file1 should not be in root children"


@pytest.mark.asyncio
async def test_file_rename_and_move(setup_file_project):
    project_node, repos, arangodb_client, project_path = setup_file_project

    # Build initial tree
    tree_before = await _build_and_get_tree(project_node, repos, arangodb_client)
    assert tree_before, "No tree nodes built"

    project_name = project_node.name

    # Create a folder to move file into
    target_folder = project_path / "subfolder"
    target_folder.mkdir(exist_ok=True)
    (target_folder / "__init__.py").write_text("")

    # Move "file1.py" -> "subfolder/renamed_file.py"
    src = project_path / "file1.py"
    dst = target_folder / "renamed_file.py"

    # Verify file exists before move
    file1_before = find_node_by_qname(tree_before, f"{project_name}.file1")
    assert file1_before is not None, "file1 should exist before move"

    shutil.move(src, dst)

    # Resync and get updated tree
    tree_after = await _resync_and_get_tree(project_node, repos, arangodb_client)

    # Check tree structure - old location should not exist
    file1_old = find_node_by_qname(tree_after, f"{project_name}.file1")
    assert file1_old is None, "file1 should not exist in old location"

    # Check tree structure - new location with new name should exist
    renamed_file = find_node_by_qname(
        tree_after, f"{project_name}.subfolder.renamed_file"
    )
    assert renamed_file is not None, "renamed_file should exist in new location"
    assert renamed_file.__class__.__name__ == "FileTreeNode", "renamed_file should be a file"

    # Verify parent relationships
    subfolder_node = find_node_by_qname(
        tree_after, f"{project_name}.subfolder")
    assert subfolder_node is not None
    subfolder_children = (
        subfolder_node.children if hasattr(subfolder_node, "children") else []
    )
    child_names = [getattr(c, "name", None) for c in subfolder_children]
    assert "renamed_file" in child_names, "renamed_file should be in subfolder children"

    # Verify it's not in root children

    root_child_names = [getattr(c, "name", None) for c in tree_after]
    assert "file1" not in root_child_names, "file1 should not be in root children"
