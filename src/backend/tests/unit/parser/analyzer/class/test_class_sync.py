import shutil
from pathlib import Path
from typing import List

import pytest
import pytest_asyncio

from app.core.builder.tree_builder import TreeBuilder
from app.core.parser.graph_builder.orchestrator import GraphBuilderOrchestrator
from app.core.schemas.tree import AnyTreeNode
from app.core.services.project_service import ProjectService

SAMPLES_PATH = Path(__file__).parent / "sample_class"
PROJECT_NAME = "sample_class"


def _find_node_by_name(nodes: List[AnyTreeNode], name: str):
    return next((n for n in nodes if getattr(n, "name", None) == name), None)


def _find_node_by_name_recursive(
    nodes: List[AnyTreeNode], name: str
) -> AnyTreeNode:
    for node in nodes:
        if getattr(node, "name", None) == name:
            return node
        if hasattr(node, "children") and node.children:
            found = _find_node_by_name_recursive(node.children, name)
            if found:
                return found
    return None


@pytest_asyncio.fixture
async def setup_project(tmp_path, empty_project_uow):
    project_path = tmp_path / "project"
    shutil.copytree(SAMPLES_PATH, project_path)

    project_service = ProjectService(empty_project_uow)

    project_node = await project_service.create(
        PROJECT_NAME, "Test Project", str(project_path)
    )
    empty_project_uow.project = project_node

    yield project_node, empty_project_uow, project_path
    await project_service.delete(project_node.id)
    shutil.rmtree(project_path)


def _read_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _write_file(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def _append_sync_block(path: Path) -> None:
    block = (
        "\n\n# SYNC_TEST_START\n\nclass SyncAddedClass:\n    pass\n"
        "# SYNC_TEST_END\n"
    )
    with path.open("a", encoding="utf-8") as f:
        f.write(block)


def _remove_sync_block(content: str, start_str: str, end_str: str) -> str:
    start = content.find(start_str)
    if start == -1:
        return content
    end = content.find(end_str, start)
    if end == -1:
        return content
    end_line = content.find("\n", end)
    if end_line == -1:
        end_line = len(content)
    return content[:start] + content[end_line:]


async def _build_and_get_tree(project_node, pow):
    orchestrator = GraphBuilderOrchestrator(
        project_node,
        pow
    )
    await orchestrator.resync()

    project_service = ProjectService(pow)
    # project = await project_service.get(project_node.id)
    # assert project is not None, "Project not found after build"

    children = await project_service.get_children()
    tree_builder = TreeBuilder(children)
    return tree_builder.build()


async def _resync_and_get_tree(project_node, pow):
    orchestrator = GraphBuilderOrchestrator(
        project_node,
        uow=pow,
    )
    await orchestrator.resync()

    project_service = ProjectService(pow)

    children = await project_service.get_children()
    tree_builder = TreeBuilder(children)
    return tree_builder.build()


@pytest.mark.asyncio
async def test_class_sync_add_and_remove(setup_project):
    project_node, project_uow, project_path = setup_project
    target_file = project_path / "main.py"

    # 1) Build once
    tree = await _build_and_get_tree(
        project_node, project_uow
    )
    assert tree, "No tree nodes built"

    file_node = tree[0]

    # Snapshot current children names (unused, but ensures access is valid)
    _ = [getattr(c, "name", None) for c in file_node.children]

    original = _read_file(target_file)
    try:
        # 2) Append a class to the file
        _append_sync_block(target_file)

        # 3) Resync and verify class is present
        tree_after_add = await _resync_and_get_tree(
            project_node, project_uow
        )
        file_node_after_add = tree_after_add[0]
        names_after_add = [
            getattr(c, "name", None) for c in file_node_after_add.children
        ]

        assert "SyncAddedClass" in names_after_add, (
            "New class not detected after resync"
        )

        # 4) Remove the class and resync
        updated = _remove_sync_block(
            _read_file(target_file),
            start_str="class SyncAddedClass:",
            end_str="pass",
        )
        _write_file(target_file, updated)

        tree_after_remove = await _resync_and_get_tree(
            project_node, project_uow
        )
        file_node_after_remove = tree_after_remove[0]
        names_after_remove = [
            getattr(c, "name", None) for c in file_node_after_remove.children
        ]
        assert "SyncAddedClass" not in names_after_remove, (
            "Removed class still present after resync"
        )

    finally:
        # Restore original content
        _write_file(target_file, original)
        # Final resync to leave DB in original state
        await _resync_and_get_tree(
            project_node, project_uow
        )


@pytest.mark.asyncio
async def test_class_sync_add_and_remove_inside_class(setup_project):
    project_node, project_uow, project_path = setup_project
    target_file = project_path / "main.py"

    # 1) Build once to ensure project is in the DB
    tree = await _build_and_get_tree(
        project_node, project_uow
    )
    assert tree, "No tree nodes built"

    # 2) Find the target class to modify
    parent_class = _find_node_by_name_recursive(tree, "Parent")
    assert parent_class is not None, "'Parent' class not found"
    assert hasattr(
        parent_class, "code_position"), "Node has no position attribute"

    # Use the position to insert new code block
    end_line = parent_class.code_position.end_line_no
    indent = parent_class.code_position.col_offset + 4

    def _insert_block(path: Path):
        lines = _read_file(path).splitlines()
        block = [
            f"{' ' * indent}# SYNC_TEST_START\n\n",
            f"{' ' * indent}class SyncAddedInner:",
            f"{' ' * (indent+4)}pass",
            f"{' ' * indent}# SYNC_TEST_END",
        ]
        # Insert before the last line of the class's body
        lines[end_line:end_line] = block

        _write_file(path, "\n".join(lines))

    original_content = _read_file(target_file)
    try:
        # 3) Insert new inner class and resync
        _insert_block(target_file)

        tree_after_add = await _resync_and_get_tree(
            project_node, project_uow
        )
        parent_after_add = _find_node_by_name_recursive(
            tree_after_add, "Parent")

        assert "SyncAddedInner" in [
            getattr(c, "name", None) for c in parent_after_add.children
        ], "New inner class not detected in 'Parent'"

        # 4) Remove the inner class and resync
        content_with_block = _read_file(target_file)
        content_without_block = _remove_sync_block(
            content_with_block,
            start_str="class SyncAddedInner:",
            end_str="pass",
        )
        _write_file(target_file, content_without_block)

        tree_after_remove = await _resync_and_get_tree(
            project_node, project_uow
        )
        parent_after_remove = _find_node_by_name_recursive(
            tree_after_remove, "Parent")
        assert "SyncAddedInner" not in [
            getattr(c, "name", None) for c in parent_after_remove.children
        ], "Removed inner class still present"

    finally:
        # 5) Restore original content and resync
        _write_file(target_file, original_content)
        await _resync_and_get_tree(
            project_node, project_uow
        )
