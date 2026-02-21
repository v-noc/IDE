import shutil
from pathlib import Path
from typing import List

import pytest
import pytest_asyncio

from app.core.builder.tree_builder import TreeBuilder
from app.core.model.nodes import ProjectNode
from app.core.parser.graph_builder.orchestrator import GraphBuilderOrchestrator
from app.core.repository import Repositories
from app.core.schemas.tree import AnyTreeNode, FunctionTreeNode
from app.core.services.project_service import ProjectService

FIXTURE_PROJECT = Path(__file__).parent / "simple_function"
PROJECT_NAME = "simple_function"


@pytest_asyncio.fixture
async def setup_project(tmp_path, create_repos, terminusdb_client):
    project_path = tmp_path / "project"
    shutil.copytree(FIXTURE_PROJECT, project_path)

    project_service = ProjectService(create_repos)
    project_node = await project_service.create(
        name=PROJECT_NAME,
        path=str(project_path),
        description="Test Project",
    )

    yield project_node, create_repos, project_path, terminusdb_client
    await project_service.delete(project_node.id)
    shutil.rmtree(project_path)


def find_node_by_name(nodes: List[AnyTreeNode], name: str):
    return next((node for node in nodes if node.qname.split(".")[-1] == name), None)


def find_node_by_qname_recursive(nodes: List[AnyTreeNode], qname: str):
    for node in nodes:
        if node.qname == qname:
            return node
        if hasattr(node, "children") and node.children:
            found = find_node_by_qname_recursive(node.children, qname)
            if found:
                return found
    return None


def find_node_by_name_recursive(nodes: List[AnyTreeNode], name: str) -> AnyTreeNode:
    for node in nodes:
        if getattr(node, "name", None) == name and isinstance(node, FunctionTreeNode):
            return node
        if hasattr(node, "children") and node.children:
            found = find_node_by_name_recursive(node.children, name)
            if found:
                return found
    return None


def _read_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _write_file(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def _append_sync_block(path: Path) -> None:
    block = (
        "\n\n# SYNC_TEST_START\n\ndef sync_added():\n    return 42\n# SYNC_TEST_END\n"
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


async def _build_and_get_tree(project_node, create_repos, db):
    orchestrator = GraphBuilderOrchestrator(
        project_node,
        db=db,
    )
    await orchestrator.resync()

    project_service = ProjectService(create_repos)

    children = await project_service.get_children(project_node.db_name)
    tree_builder = TreeBuilder(children)
    return tree_builder.build()


async def _resync_and_get_tree(project_node, repos, db):
    orchestrator = GraphBuilderOrchestrator(
        project_node,
        db=db,
    )
    await orchestrator.resync()

    project_service = ProjectService(repos)
    children = await project_service.get_children(project_node.db_name)
    tree_builder = TreeBuilder(children)
    return tree_builder.build()


@pytest.mark.asyncio
async def test_function_sync_add_and_remove(setup_project):
    project_node, create_repos, project_path, terminusdb_client = setup_project
    target_file = project_path / "main.py"

    # 1) Build once
    tree = await _build_and_get_tree(project_node, create_repos, terminusdb_client)
    assert tree, "No tree nodes built"

    original = _read_file(target_file)
    try:
        # 2) Append a function to the file
        _append_sync_block(target_file)

        # 3) Resync and verify function is present
        tree_after_add = await _resync_and_get_tree(
            project_node, create_repos, terminusdb_client
        )
        file_node_after_add = tree_after_add[0]
        names_after_add = [
            getattr(c, "name", None) for c in file_node_after_add.children
        ]
        assert "sync_added" in names_after_add, "New function not detected after resync"

        # 4) Remove the function and resync
        updated = _remove_sync_block(
            _read_file(target_file), start_str="def sync_added():", end_str="return 42"
        )
        _write_file(target_file, updated)

        tree_after_remove = await _resync_and_get_tree(
            project_node, create_repos, terminusdb_client
        )
        file_node_after_remove = tree_after_remove[1]
        # Debug helper (kept commented to avoid noisy output / lint issues):
        # for child in file_node_after_remove.children:
        #     print(
        #         f"Child: {child.name}, Status: {child.status} "
        #         f"type: {child.node_type}"
        #     )
        names_after_remove = [
            getattr(c, "name", None) for c in file_node_after_remove.children
        ]
        assert "sync_added" not in names_after_remove, (
            "Removed function still present after resync"
        )

    finally:
        # Restore original content
        _write_file(target_file, original)
        # Final resync to leave DB in original state
        await _resync_and_get_tree(project_node, create_repos, terminusdb_client)


@pytest.mark.asyncio
async def test_function_sync_add_and_remove_inside_function(setup_project):
    project_node, create_repos, project_path, terminusdb_client = setup_project
    target_file = project_path / "main.py"

    # 1) Build once to ensure project is in the DB
    tree = await _build_and_get_tree(project_node, create_repos, terminusdb_client)
    assert tree, "No tree nodes built"

    # 2) Find the target function to modify
    add_func_node = find_node_by_name_recursive(tree, "add")
    assert add_func_node is not None, "'add' function not found"
    assert hasattr(
        add_func_node, "code_position"), "Node has no position attribute"

    # Use the position to insert new code block
    end_line = add_func_node.code_position.end_line_no
    indent = add_func_node.code_position.col_offset + 4

    def _insert_block(path: Path):
        lines = _read_file(path).splitlines()
        block = [
            f"{' ' * indent}# SYNC_TEST_START\n\n",
            f"{' ' * indent}def sync_added_inside():",
            f"{' ' * indent}    pass\n",
            f"{' ' * indent}# SYNC_TEST_END",
        ]
        # Insert before the last line of the function's body
        lines[end_line - 1: end_line - 1] = block
        _write_file(path, "\n".join(lines))

    original_content = _read_file(target_file)
    try:
        # 3) Insert new function and resync
        _insert_block(target_file)

        tree_after_add = await _resync_and_get_tree(
            project_node, create_repos, terminusdb_client
        )
        add_func_after_add = find_node_by_qname_recursive(
            tree_after_add, "simple_function.main.factory.add"
        )

        assert "sync_added_inside" in [
            getattr(c, "name", None) for c in add_func_after_add.children
        ], "New function not detected in 'add'"

        # 4) Remove the new function and resync
        content_with_block = _read_file(target_file)
        content_without_block = _remove_sync_block(
            content_with_block, start_str="def sync_added_inside():", end_str="pass"
        )
        _write_file(target_file, content_without_block)

        tree_after_remove = await _resync_and_get_tree(
            project_node, create_repos, terminusdb_client
        )
        add_func_after_remove = find_node_by_qname_recursive(
            tree_after_remove, "simple_function.main.factory.add"
        )
        assert "sync_added_inside" not in [
            getattr(c, "name", None) for c in add_func_after_remove.children
        ], "Removed function still present"

    finally:
        # 5) Restore original content and resync
        _write_file(target_file, original_content)
        await _resync_and_get_tree(project_node, create_repos, terminusdb_client)
