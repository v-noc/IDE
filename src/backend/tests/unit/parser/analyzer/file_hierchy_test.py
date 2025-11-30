from pathlib import Path
import shutil

from app.core.parser.scope_manager.manager import ScopeManager
from app.core.parser.graph_builder.discovery.scanner import FileScanner
from app.core.parser.graph_builder.collection.hierarchy import HierarchyBuilder
from app.core.model.nodes import ProjectNode

FIXTURE_PROJECT = Path(__file__).parent / "simple_project"
PROJECT_NAME = "sample_project"
IGNORE_FILE = "v-noc.toml"


def _build_sample_hierarchy(tmp_path):
    project_path = tmp_path / "project"
    shutil.copytree(FIXTURE_PROJECT, project_path)

    ignored_file = project_path / "build" / "ignored.py"
    ignored_file.write_text("")

    db_path = tmp_path / "db" / PROJECT_NAME
    db_path.parent.mkdir(parents=True, exist_ok=True)

    scope_manager = ScopeManager(PROJECT_NAME, db_path=str(db_path))
    scanner = FileScanner(str(project_path), ignore_file_name=IGNORE_FILE)
    scan_result = scanner.scan()

    project_node = ProjectNode(
        name=PROJECT_NAME,
        path=str(project_path),
        qname=PROJECT_NAME,
        description="Test Project",
    )
    builder = HierarchyBuilder(project_node, scope_manager)

    for file_path, checksum in scan_result.files.items():
        rel_path = Path(file_path).relative_to(project_path)
        builder.build_hierarchy(rel_path, checksum)

    return scope_manager, scan_result, project_path


def test_hierarchy_and_ignore(tmp_path):
    scope_manager, scan_result, project_path = _build_sample_hierarchy(
        tmp_path
    )

    scanned_paths = [
        Path(p).relative_to(project_path).as_posix()
        for p in scan_result.files.keys()
    ]
    expected_paths = {
        "main.py",
        "core/user.py",
        "core/post.py",
        "core/data/user.py",
        "app/api.py",
    }
    assert set(scanned_paths) == expected_paths
    assert "build/ignored.py" not in scanned_paths

    scanned_folders = {
        Path(folder).relative_to(project_path).as_posix()
        for folder in scan_result.folders
        if folder != str(project_path)
    }
    assert f"core" in scanned_folders
    assert f"core/data" in scanned_folders
    assert f"app" in scanned_folders

    root = scope_manager.get_scope_by_qname(PROJECT_NAME)
    assert root is not None
    assert root.type.value == "folder"

    main = scope_manager.get_scope_by_qname(f"{PROJECT_NAME}.main")
    assert main is not None and main.type.value == "file"

    core_scope = scope_manager.get_scope_by_qname(f"{PROJECT_NAME}.core")
    assert core_scope is not None and core_scope.type.value == "folder"

    core_user = scope_manager.get_scope_by_qname(f"{PROJECT_NAME}.core.user")
    assert core_user is not None and core_user.type.value == "file"

    core_post = scope_manager.get_scope_by_qname(f"{PROJECT_NAME}.core.post")
    assert core_post is not None and core_post.type.value == "file"

    core_data = scope_manager.get_scope_by_qname(f"{PROJECT_NAME}.core.data")
    assert core_data is not None and core_data.type.value == "folder"

    core_data_user = scope_manager.get_scope_by_qname(
        f"{PROJECT_NAME}.core.data.user"
    )
    assert core_data_user is not None and core_data_user.type.value == "file"

    app_scope = scope_manager.get_scope_by_qname(f"{PROJECT_NAME}.app")
    assert app_scope is not None and app_scope.type.value == "folder"

    app_api = scope_manager.get_scope_by_qname(f"{PROJECT_NAME}.app.api")
    assert app_api is not None and app_api.type.value == "file"

    build_scope = scope_manager.get_scope_by_qname(f"{PROJECT_NAME}.build")
    assert build_scope is None, "Build folder should not exist in DB"


def test_scope_contains_links(tmp_path):
    scope_manager, _, _ = _build_sample_hierarchy(tmp_path)

    root = scope_manager.get_scope_by_qname(PROJECT_NAME)
    assert root is not None

    root_children = {
        child.name: child for child in scope_manager.get_children(root.id)
    }
    assert set(root_children.keys()) == {"main", "core", "app"}
    assert root_children["main"].type.value == "file"
    assert root_children["core"].type.value == "folder"
    assert root_children["app"].type.value == "folder"

    core_children = {
        child.name: child for child in scope_manager.get_children(
            root_children["core"].id
        )
    }
    assert set(core_children.keys()) == {"user", "post", "data"}
    assert core_children["user"].type.value == "file"
    assert core_children["post"].type.value == "file"
    assert core_children["data"].type.value == "folder"

    data_children = scope_manager.get_children(core_children["data"].id)
    assert len(data_children) == 1
    assert data_children[0].name == "user"
    assert data_children[0].type.value == "file"


def test_delete_scope_cascades(tmp_path):
    scope_manager, _, _ = _build_sample_hierarchy(tmp_path)

    core_scope = scope_manager.get_scope_by_qname(f"{PROJECT_NAME}.core")
    assert core_scope is not None

    core_user = scope_manager.get_scope_by_qname(f"{PROJECT_NAME}.core.user")
    assert core_user is not None

    scope_manager.delete_scope(core_scope.id)

    assert scope_manager.get_scope_by_qname(f"{PROJECT_NAME}.core") is None
    assert scope_manager.get_scope_by_qname(
        f"{PROJECT_NAME}.core.user") is None

    root = scope_manager.get_scope_by_qname(PROJECT_NAME)
    remaining_children = {
        child.name for child in scope_manager.get_children(root.id)
    }
    assert "core" not in remaining_children
