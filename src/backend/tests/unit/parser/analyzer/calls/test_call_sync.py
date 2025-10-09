from pathlib import Path
from typing import List

from app.core.repository import Repositories
from app.core.services.project_service import ProjectService
from app.core.parser.graph_builder import GraphBuilder
from app.core.builder.tree_builder import TreeBuilder
from app.core.schemas.tree import AnyTreeNode


# Locate sample project directory used by this test
CURRENT_FILE = Path(__file__).resolve()
PROJECT_PATH = (CURRENT_FILE.parent / "./simple_calls").absolute()
TARGET_FILE = PROJECT_PATH / "main.py"


def _find_node_by_name(nodes: List[AnyTreeNode], name: str):
    return next(
        (
            node
            for node in nodes
            if getattr(node, "name", None) == name
        ),
        None,
    )


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


def _read_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _write_file(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def _build_and_get_tree(db):
    builder = GraphBuilder(
        project_path=PROJECT_PATH.as_posix(),
        project_node=None,
        db=db,
    )
    builder.build("CallSync", "Call sync test project.")

    repos = Repositories(db)
    project_service = ProjectService(repos)
    projects = project_service.get_all()
    assert projects, "No project found after build"

    children = project_service.get_children(projects[0].id)
    tree_builder = TreeBuilder(children)
    return tree_builder.build()


def _resync_and_get_tree(db):
    repos = Repositories(db)
    project_service = ProjectService(repos)
    projects = project_service.get_all()
    assert projects, "No project found before resync"

    builder = GraphBuilder(
        project_path=PROJECT_PATH.as_posix(),
        project_node=projects[0],
        db=db,
    )
    builder.build(projects[0].name, projects[0].description)

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
    return [
        c for c in getattr(node, "children", []) if c.node_type == "call"
    ]


def _has_call_named(node: AnyTreeNode, name: str) -> bool:
    return any(
        getattr(c, "name", None) == name for c in _get_call_children(node)
    )


def _has_nested_call_with_name(node: AnyTreeNode, name_pred: str) -> bool:
    for c in _get_call_children(node):
        for gc in getattr(c, "children", []) or []:
            if getattr(gc, "node_type", None) == "call" and (
                getattr(gc, "name", "") == name_pred
                or name_pred in getattr(gc, "name", "")
            ):
                return True
    return False


def test_call_sync_add_and_remove(arangodb_client, tmp_path):
    # Prepare initial file content (ensures idempotency for local runs)
    PROJECT_PATH.mkdir(parents=True, exist_ok=True)
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
    _write_file(TARGET_FILE, initial_code)

    # 1) Build once
    tree = _build_and_get_tree(arangodb_client)
    file_node = _get_file_node(tree)

    # There should be exactly one top-level 'reader' call under the file
    calls = _get_call_children(file_node)
    assert (
        len([c for c in calls if getattr(c, "name", None) == "reader"]) == 1
    )

    # 2) Append a new call reader(FileReader()) and resync
    original = _read_file(TARGET_FILE)
    try:
        _append_reader_call(TARGET_FILE)
        tree_after_add = _resync_and_get_tree(arangodb_client)
        file_after_add = _get_file_node(tree_after_add)

        # Still only one 'reader' call under file (no duplicates)
        calls_after_add = _get_call_children(file_after_add)
        count_reader = len([
            c for c in calls_after_add
            if getattr(c, "name", None) == "reader"
        ])
        assert count_reader == 1, (
            "Duplicate 'reader' call created"
        )

        # And nested call to FileReader.read should exist under the reader call
        # Display name for methods is formatted as '(ClassName).method'
        assert _has_nested_call_with_name(
            file_after_add, "(FileReader).read"
        ), "Expected nested call to FileReader.read not found"

        # 3) Remove the extra call and resync
        updated = _remove_reader_call(_read_file(TARGET_FILE))
        _write_file(TARGET_FILE, updated)

        tree_after_remove = _resync_and_get_tree(arangodb_client)
        file_after_remove = _get_file_node(tree_after_remove)

        # The nested FileReader.read call should be gone
        nested_exists = _has_nested_call_with_name(
            file_after_remove, "(FileReader).read"
        )
        assert not nested_exists, "Removed FileReader.read call still present"

        # Still exactly one top-level 'reader' call
        calls_after_remove = _get_call_children(file_after_remove)
        remaining_reader = len(
            [
                c
                for c in calls_after_remove
                if getattr(c, "name", None) == "reader"
            ]
        )
        assert remaining_reader == 1
    finally:
        # Restore original file content and resync
        _write_file(TARGET_FILE, original)
        _resync_and_get_tree(arangodb_client)
