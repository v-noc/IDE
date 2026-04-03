import shutil
from pathlib import Path
from typing import List

import pytest
import pytest_asyncio

from app.core.builder.tree_builder import TreeBuilder
from app.core.model.nodes import ProjectNode
from app.core.parser.graph_builder.orchestrator import GraphBuilderOrchestrator
from app.core.repository import Repositories
from app.core.schemas.tree import AnyTreeNode
from app.core.services.project_service import ProjectService

FIXTURE_PROJECT = Path(__file__).parent / "simple_calls"
PROJECT_NAME = "simple_calls"


def _find_node_by_name(nodes: List[AnyTreeNode], name: str):
    return next(
        (node for node in nodes if getattr(node, "name", None) == name),
        None,
    )


def _find_node_by_name_recursive(nodes: List[AnyTreeNode], name: str) -> AnyTreeNode:
    for node in nodes:
        if getattr(node, "name", None) == name and not node.id.startswith("CallSchema/"):
            return node
        if hasattr(node, "children") and node.children:
            found = _find_node_by_name_recursive(node.children, name)
            if found:
                return found
    return None


def _read_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _write_file(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


async def _build_and_get_tree(project_uow):

    orchestrator = GraphBuilderOrchestrator(
        project_uow.project,
        uow=project_uow,

    )
    await orchestrator.resync()

    project_service = ProjectService(project_uow)

    children, _ = await project_service.get_children()

    tree_builder = TreeBuilder(children)
    return tree_builder.build()


async def _resync_and_get_tree(project_uow):
    orchestrator = GraphBuilderOrchestrator(
        project_uow.project,
        uow=project_uow,
    )
    await orchestrator.resync()

    project_service = ProjectService(project_uow)

    children, _ = await project_service.get_children()
    tree_builder = TreeBuilder(children)
    return tree_builder.build()


def _append_reader_call(path: Path) -> None:
    with path.open("a", encoding="utf-8") as f:
        f.write("\nfr = FileReader()\nreader(fr)\n")


def _remove_reader_call(content: str) -> str:
    lines = content.splitlines()
    new_lines = [
        line
        for line in lines
        if line.strip() not in ("fr = FileReader()", "reader(fr)")
    ]
    return "\n".join(new_lines) + ("\n" if content.endswith("\n") else "")


def _get_file_node(tree: List[AnyTreeNode]) -> AnyTreeNode:
    assert tree, "No tree nodes built"
    for node in tree:
        if (
            getattr(node, "node_type", None) == "file"
            and getattr(node, "name", None) == "main"
        ):
            return node
    return tree[0]


def _get_call_children(node: AnyTreeNode) -> List[AnyTreeNode]:
    return [c for c in getattr(node, "children", []) if c.id.startswith("CallSchema/")]


def _has_call_named(node: AnyTreeNode, name: str) -> bool:
    return any(getattr(c, "name", None) == name for c in _get_call_children(node))


def _get_call_child_by_name(node: AnyTreeNode, name: str) -> AnyTreeNode | None:
    for c in _get_call_children(node):
        if getattr(c, "name", None) == name:
            return c
    return None


def _get_call_child_by_qname(node: AnyTreeNode, qname: str) -> AnyTreeNode | None:
    for c in _get_call_children(node):
        if getattr(c, "qname", None) == qname:
            return c
    return None


def _has_nested_call_with_name(node: AnyTreeNode, name_pred: str) -> bool:
    for c in _get_call_children(node):
        for gc in getattr(c, "children", []) or []:
            if gc.id.startswith("CallSchema/") and (
                getattr(gc, "qname", "") == name_pred
                or name_pred in getattr(gc, "qname", "")
            ):
                return True
    return False


@pytest_asyncio.fixture
async def setup_project(tmp_path, empty_project_uow, terminusdb_client):
    project_path = tmp_path / "simple_calls"
    shutil.copytree(FIXTURE_PROJECT, project_path)

    project_service = ProjectService(empty_project_uow)
    project_node = await project_service.create(
        PROJECT_NAME, "Test Project", str(project_path)
    )
    empty_project_uow.project = project_node
    yield project_node, empty_project_uow, terminusdb_client, project_path
    await project_service.delete(project_node.id)
    shutil.rmtree(project_path)


@pytest.mark.asyncio
async def test_call_sync_add_and_remove(setup_project):
    project_node, project_uow, terminusdb_client, project_path = setup_project
    target_file = project_path / "main.py"

    # Prepare initial file content (ensures idempotency for local runs)
    initial_code = (
        "def reader(doc):\n"
        "    doc.read()\n\n"
        "class Document:\n"
        "    def read(self):\n"
        "        pass\n\n"
        "class FileReader:\n"
        "    def read(self, file_name: str):\n"
        "        pass\n\n"
        "a = Document()\n"
        "reader(a)\n"
    )
    _write_file(target_file, initial_code)

    # 1) Build once
    tree = await _build_and_get_tree(project_uow)

    file_node = _get_file_node(tree)

    # There should be exactly one top-level 'reader' call under the file
    calls = _get_call_children(file_node)
    assert len([c for c in calls if getattr(c, "name", None) == "reader"]) == 1

    # 2) Append a new call reader(FileReader()) and resync
    original = _read_file(target_file)
    try:
        _append_reader_call(target_file)
        tree_after_add = await _resync_and_get_tree(
            project_uow
        )
        file_after_add = _get_file_node(tree_after_add)

        # Still only one 'reader' call under file (no duplicates)
        calls_after_add = _get_call_children(file_after_add)
        count_reader = len(
            [c for c in calls_after_add if getattr(
                c, "name", None) == "reader"]
        )
        assert count_reader == 1, "Duplicate 'reader' call created"

        # Get function and method nodes to construct qnames dynamically
        reader_func = _find_node_by_name_recursive(
            file_after_add.children, "reader")
        assert reader_func is not None, "reader function not found"

        # Find Document.read method
        document_class = _find_node_by_name_recursive(
            file_after_add.children, "Document"
        )
        assert document_class is not None, "Document class not found"
        document_read_method = _find_node_by_name_recursive(
            document_class.children, "read"
        )
        assert document_read_method is not None, "Document.read method not found"

        # Find FileReader.read method
        filereader_class = _find_node_by_name_recursive(
            file_after_add.children, "FileReader"
        )
        assert filereader_class is not None, "FileReader class not found"
        filereader_read_method = _find_node_by_name_recursive(
            filereader_class.children, "read"
        )
        assert filereader_read_method is not None, "FileReader.read method not found"

        # And nested call to FileReader.read should exist under the reader call
        reader_call = ""
        for i in calls_after_add:
            if i.name == "reader":
                reader_call = i
                break

        # Display name for methods is formatted as '(ClassName).method'
        filereader_read_call_qname = f"{reader_call.id}::{filereader_read_method.id}"
        assert _has_nested_call_with_name(
            file_after_add,
            filereader_read_call_qname,
        ), "Expected nested call to FileReader.read not found"

        # Reader call should have two nested calls now: Document.read and

        assert reader_call is not None, "reader call node not found"
        reader_nested_calls = [
            gc
            for gc in getattr(reader_call, "children", []) or []
            if gc.id.startswith("CallSchema/")
        ]
        assert len(reader_nested_calls) == 2, (
            "reader should have two nested calls after adding FileReader"
        )
        nested_names = {getattr(n, "qname", "") for n in reader_nested_calls}
        document_read_call_qname = f"{reader_call.id}::{document_read_method.id}"
        assert document_read_call_qname in nested_names, (
            "Document.read not found under reader"
        )
        assert filereader_read_call_qname in nested_names, (
            "FileReader.read not found under reader"
        )

        # Record the created nested call node id/key so we can assert it gets

        file_reader_call_qname = filereader_read_call_qname

        # file_reader_call_node = await repos.call_repo.find_one(
        #     {"qname": file_reader_call_qname}
        # )
        # assert file_reader_call_node is not None, (
        #     "Expected FileReader.read call node to exist in DB"
        # )
        # created_file_reader_call_key = file_reader_call_node.key
        # assert file_reader_call_node.status == "active"

        # 3) Remove the extra call and resync
        updated = _remove_reader_call(_read_file(target_file))
        _write_file(target_file, updated)

        tree_after_remove = await _resync_and_get_tree(
            project_uow
        )
        file_after_remove = _get_file_node(tree_after_remove)

        # Get function and method nodes again for the remove phase
        reader_func_remove = _find_node_by_name_recursive(
            file_after_remove.children, "reader"
        )
        assert reader_func_remove is not None, "reader function not found"

        document_class_remove = _find_node_by_name_recursive(
            file_after_remove.children, "Document"
        )
        assert document_class_remove is not None, "Document class not found"
        document_read_method_remove = _find_node_by_name_recursive(
            document_class_remove.children, "read"
        )
        assert document_read_method_remove is not None, "Document.read method not found"

        filereader_class_remove = _find_node_by_name_recursive(
            file_after_remove.children, "FileReader"
        )
        assert filereader_class_remove is not None, "FileReader class not found"
        filereader_read_method_remove = _find_node_by_name_recursive(
            filereader_class_remove.children, "read"
        )
        assert filereader_read_method_remove is not None, (
            "FileReader.read method not found"
        )

        # The nested FileReader.read call should be gone
        filereader_read_call_qname_remove = (
            f"{reader_call.id}::{filereader_read_method_remove.id}"
        )
        nested_exists = _has_nested_call_with_name(
            file_after_remove,
            filereader_read_call_qname_remove,
        )
        assert not nested_exists, "Removed FileReader.read call still present"

        # But it should still exist in DB and be marked orphaned
        # orphaned_file_reader_call_node = await repos.call_repo.find_one(
        #     {"qname": file_reader_call_qname}
        # )
        # assert orphaned_file_reader_call_node is not None
        # assert orphaned_file_reader_call_node.key == created_file_reader_call_key
        # assert orphaned_file_reader_call_node.status == "orphaned"

        # Document.read should still be present
        document_read_call_qname_remove = (
            f"{reader_call.id}::{document_read_method_remove.id}"
        )
        assert _has_nested_call_with_name(
            file_after_remove,
            document_read_call_qname_remove,
        ), "Document.read missing after removal"

        # Still exactly one top-level 'reader' call
        calls_after_remove = _get_call_children(file_after_remove)
        remaining_reader = len(
            [c for c in calls_after_remove if getattr(
                c, "name", None) == "reader"]
        )
        assert remaining_reader == 1

    finally:
        # Restore original file content and resync
        _write_file(target_file, original)
        await _resync_and_get_tree(project_uow)
