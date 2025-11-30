import shutil
from pathlib import Path

from app.core.model.nodes import ProjectNode
from app.core.parser.graph_builder.collection.hierarchy import HierarchyBuilder
from app.core.parser.graph_builder.discovery.scanner import FileScanner
from app.core.parser.graph_builder.discovery.change_detector import ChangeDetector
from app.core.parser.scope_manager.manager import ScopeManager


FIXTURE_PROJECT = Path(__file__).resolve().parents[1] / "analyzer" / "simple_project"
PROJECT_NAME = "sample_project"
IGNORE_FILE = "v-noc.toml"


def _bootstrap_project(tmp_path):
    project_path = tmp_path / "project"
    shutil.copytree(FIXTURE_PROJECT, project_path)

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

    return project_path, scope_manager, scanner


def test_change_detector_tracks_folder_additions(tmp_path):
    project_path, scope_manager, scanner = _bootstrap_project(tmp_path)
    detector = ChangeDetector(scope_manager)

    new_dir = project_path / "features" / "beta"
    new_dir.mkdir(parents=True)
    new_file = new_dir / "logic.py"
    new_file.write_text("def feature():\n    return 'ok'\n")

    change_set = detector.detect_changes(scanner.scan())

    assert new_file.as_posix() in change_set.new_files
    assert change_set.has_changes()
    assert change_set.has_folder_changes()

    new_folder_paths = set(change_set.new_folders)
    assert str(new_dir.parent) in new_folder_paths
    assert str(new_dir) in new_folder_paths


def test_change_detector_tracks_folder_deletions(tmp_path):
    project_path, scope_manager, scanner = _bootstrap_project(tmp_path)
    detector = ChangeDetector(scope_manager)

    shutil.rmtree(project_path / "core" / "data")

    change_set = detector.detect_changes(scanner.scan())

    deleted_folder_paths = set(change_set.deleted_folders)
    assert any(path.endswith("core/data") for path in deleted_folder_paths)
    assert change_set.deleted_files
    assert change_set.has_folder_changes()

