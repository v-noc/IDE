from pathlib import Path
from typing import List

from app.core.repository import Repositories
from app.core.services.project_service import ProjectService
from app.core.parser.graph_builder import GraphBuilder
from app.core.builder.tree_builder import TreeBuilder
from app.core.schemas.tree import AnyTreeNode


# Locate sample project directory used by other tests
CURRENT_FILE = Path(__file__).resolve()
PROJECT_PATH = (CURRENT_FILE.parent / "./simple_function").absolute()
TARGET_FILE = PROJECT_PATH / "main.py"


def _find_node_by_name(nodes: List[AnyTreeNode], name: str):
    return next((node for node in nodes if getattr(node, "name", None) == name), None)


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


def _append_sync_block(path: Path) -> None:
    block = (
        "\n\n# SYNC_TEST_START\n\ndef sync_added():\n    return 42\n# SYNC_TEST_END\n"
    )
    with path.open("a", encoding="utf-8") as f:
        f.write(block)


def _remove_sync_block(content: str) -> str:
    start = content.find("# SYNC_TEST_START")
    if start == -1:
        return content
    end = content.find("# SYNC_TEST_END", start)
    if end == -1:
        return content
    end_line = content.find("\n", end)
    if end_line == -1:
        end_line = len(content)
    return content[:start] + content[end_line:]


def _build_and_get_tree(db):
    # Initial or incremental build; when a project already exists we pass its node
    builder = GraphBuilder(
        project_path=PROJECT_PATH.as_posix(),
        project_node=None,
        db=db,
    )
    builder.build("Protector", "Protector is a tool for protecting your code.")

    repos = Repositories(db)
    project_service = ProjectService(repos)
    projects = project_service.get_all()
    assert projects, "No project found after build"

    children = project_service.get_children(projects[0].id)
    tree_builder = TreeBuilder(children)
    return tree_builder.build()


def _resync_and_get_tree(db):
    # Fetch existing project node and run a resync build using existing node
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


def test_function_sync_add_and_remove(arangodb_client):
    # 1) Build once
    tree = _build_and_get_tree(arangodb_client)
    assert tree, "No tree nodes built"

    file_node = tree[0]

    # Snapshot current children names
    initial_children = [getattr(c, "name", None) for c in file_node.children]

    original = _read_file(TARGET_FILE)
    try:
        # 2) Append a function to the file
        _append_sync_block(TARGET_FILE)

        # 3) Resync and verify function is present
        tree_after_add = _resync_and_get_tree(arangodb_client)
        file_node_after_add = tree_after_add[0]
        names_after_add = [
            getattr(c, "name", None) for c in file_node_after_add.children
        ]
        assert "sync_added" in names_after_add, "New function not detected after resync"

        # 4) Remove the function and resync
        updated = _remove_sync_block(_read_file(TARGET_FILE))
        _write_file(TARGET_FILE, updated)

        tree_after_remove = _resync_and_get_tree(arangodb_client)
        file_node_after_remove = tree_after_remove[0]
        names_after_remove = [
            getattr(c, "name", None) for c in file_node_after_remove.children
        ]
        assert "sync_added" not in names_after_remove, (
            "Removed function still present after resync"
        )

    finally:
        # Restore original content
        _write_file(TARGET_FILE, original)
        # Final resync to leave DB in original state
        _resync_and_get_tree(arangodb_client)


def test_function_sync_add_and_remove_inside_function(arangodb_client):
    # 1) Build once to ensure project is in the DB
    tree = _build_and_get_tree(arangodb_client)
    assert tree, "No tree nodes built"

    # 2) Find the target function to modify
    add_func_node = _find_node_by_name_recursive(tree, "add")
    assert add_func_node is not None, "'add' function not found"
    assert hasattr(add_func_node, "position"), "Node has no position attribute"

    # Use the position to insert new code block
    end_line = add_func_node.position.end_line_no
    indent = add_func_node.position.col_offset + 4

    def _insert_block(path: Path):
        lines = _read_file(path).splitlines()
        block = [
            f"{' ' * indent}# SYNC_TEST_START\n\n",
            f"{' ' * indent}def sync_added_inside(): pass",
            f"{' ' * indent}# SYNC_TEST_END",
        ]
        # Insert before the last line of the function's body
        lines[end_line - 1: end_line - 1] = block
        _write_file(path, "\n".join(lines))

    original_content = _read_file(TARGET_FILE)
    try:
        # 3) Insert new function and resync
        _insert_block(TARGET_FILE)

        tree_after_add = _resync_and_get_tree(arangodb_client)
        add_func_after_add = _find_node_by_name_recursive(
            tree_after_add, "add")
        assert "sync_added_inside" in [
            getattr(c, "name", None) for c in add_func_after_add.children
        ], "New function not detected in 'add'"

        # 4) Remove the new function and resync
        content_with_block = _read_file(TARGET_FILE)
        content_without_block = _remove_sync_block(content_with_block)
        _write_file(TARGET_FILE, content_without_block)

        tree_after_remove = _resync_and_get_tree(arangodb_client)
        add_func_after_remove = _find_node_by_name_recursive(
            tree_after_remove, "add")
        assert "sync_added_inside" not in [
            getattr(c, "name", None) for c in add_func_after_remove.children
        ], "Removed function still present"

    finally:
        # 5) Restore original content and resync
        _write_file(TARGET_FILE, original_content)
        _resync_and_get_tree(arangodb_client)
