import shutil
from pathlib import Path
from typing import List

import pytest

from app.core.builder.tree_builder import TreeBuilder
from app.core.model.nodes import ProjectNode
from app.core.parser.graph_builder.orchestrator import GraphBuilderOrchestrator
from app.core.parser.scope_manager.manager import ScopeManager
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
        if getattr(node, "name", None) == name:
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


def _build_and_get_tree(project_node, scope_manager, db):
    orchestrator = GraphBuilderOrchestrator(
        project_node,
        db=db,
        scope_manager=scope_manager,
    )
    orchestrator.resync()

    repos = Repositories(db)
    project_service = ProjectService(repos)
    projects = project_service.get_all()
    assert projects, "No project found after build"

    children = project_service.get_children(projects[0].id)
    tree_builder = TreeBuilder(children)
    return tree_builder.build()


def _resync_and_get_tree(project_node, scope_manager, db):
    repos = Repositories(db)
    project_service = ProjectService(repos)
    projects = project_service.get_all()
    assert projects, "No project found before resync"

    orchestrator = GraphBuilderOrchestrator(
        project_node,
        db=db,
        scope_manager=scope_manager,
    )
    orchestrator.resync()

    children = project_service.get_children(projects[0].id)
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
    return tree[0]


def _get_call_children(node: AnyTreeNode) -> List[AnyTreeNode]:
    return [c for c in getattr(node, "children", []) if c.node_type == "call"]


def _has_call_named(node: AnyTreeNode, name: str) -> bool:
    return any(getattr(c, "name", None) == name for c in _get_call_children(node))


def _get_call_child_by_name(node: AnyTreeNode, name: str) -> AnyTreeNode | None:
    for c in _get_call_children(node):
        if getattr(c, "name", None) == name:
            return c
    return None


def _has_nested_call_with_name(node: AnyTreeNode, name_pred: str) -> bool:
    for c in _get_call_children(node):
        for gc in getattr(c, "children", []) or []:
            if getattr(gc, "node_type", None) == "call" and (
                getattr(gc, "qname", "") == name_pred
                or name_pred in getattr(gc, "qname", "")
            ):
                return True
    return False


@pytest.fixture
def setup_project(tmp_path, arangodb_client):
    project_path = tmp_path / "simple_calls"
    shutil.copytree(FIXTURE_PROJECT, project_path)

    db_path = tmp_path / "db" / PROJECT_NAME
    db_path.parent.mkdir(parents=True, exist_ok=True)

    project_node = ProjectNode(
        name=PROJECT_NAME,
        path=str(project_path),
        qname=PROJECT_NAME,
        description="Call sync test project.",
    )
    scope_manager = ScopeManager(PROJECT_NAME, db_path=str(db_path))
    repos = Repositories(arangodb_client)
    project_service = ProjectService(repos)
    project_node = project_service.create_node(project_node)

    return project_node, scope_manager, arangodb_client, project_path


def test_call_sync_add_and_remove(setup_project):
    project_node, scope_manager, arangodb_client, project_path = setup_project
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
    tree = _build_and_get_tree(project_node, scope_manager, arangodb_client)
    file_node = _get_file_node(tree)

    # There should be exactly one top-level 'reader' call under the file
    calls = _get_call_children(file_node)
    assert len([c for c in calls if getattr(c, "name", None) == "reader"]) == 1

    # 2) Append a new call reader(FileReader()) and resync
    original = _read_file(target_file)
    try:
        _append_reader_call(target_file)
        tree_after_add = _resync_and_get_tree(
            project_node, scope_manager, arangodb_client
        )
        file_after_add = _get_file_node(tree_after_add)

        # Still only one 'reader' call under file (no duplicates)
        calls_after_add = _get_call_children(file_after_add)
        count_reader = len(
            [c for c in calls_after_add if getattr(c, "name", None) == "reader"]
        )
        assert count_reader == 1, "Duplicate 'reader' call created"

        # And nested call to FileReader.read should exist under the reader call
        # Display name for methods is formatted as '(ClassName).method'
        assert _has_nested_call_with_name(
            file_after_add,
            "simple_calls.main.reader::simple_calls.main.FileReader.read",
        ), "Expected nested call to FileReader.read not found"

        # Reader call should have two nested calls now: Document.read and
        # FileReader.read
        reader_call = _get_call_child_by_name(file_after_add, "reader")
        assert reader_call is not None, "reader call node not found"
        reader_nested_calls = [
            gc
            for gc in getattr(reader_call, "children", []) or []
            if getattr(gc, "node_type", None) == "call"
        ]
        assert len(reader_nested_calls) == 2, (
            "reader should have two nested calls after adding FileReader"
        )
        nested_names = {getattr(n, "qname", "") for n in reader_nested_calls}
        assert (
            "simple_calls.main.reader::simple_calls.main.Document.read" in nested_names
        ), "Document.read not found under reader"
        assert (
            "simple_calls.main.reader::simple_calls.main.FileReader.read"
            in nested_names
        ), "FileReader.read not found under reader"

        # 3) Remove the extra call and resync
        updated = _remove_reader_call(_read_file(target_file))
        _write_file(target_file, updated)

        tree_after_remove = _resync_and_get_tree(
            project_node, scope_manager, arangodb_client
        )
        file_after_remove = _get_file_node(tree_after_remove)

        # The nested FileReader.read call should be gone
        nested_exists = _has_nested_call_with_name(
            file_after_remove,
            "simple_calls.main.reader::simple_calls.main.FileReader.read",
        )
        assert not nested_exists, "Removed FileReader.read call still present"

        # Document.read should still be present
        assert _has_nested_call_with_name(
            file_after_remove,
            "simple_calls.main.reader::simple_calls.main.Document.read",
        ), "Document.read missing after removal"

        # Still exactly one top-level 'reader' call
        calls_after_remove = _get_call_children(file_after_remove)
        remaining_reader = len(
            [c for c in calls_after_remove if getattr(c, "name", None) == "reader"]
        )
        assert remaining_reader == 1
    finally:
        # Restore original file content and resync
        _write_file(target_file, original)
        _resync_and_get_tree(project_node, scope_manager, arangodb_client)
