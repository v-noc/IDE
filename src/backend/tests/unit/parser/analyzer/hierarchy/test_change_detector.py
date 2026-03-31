import shutil
from pathlib import Path

import pytest

from app.core.parser.driver_manager import DriverManager
from app.core.parser.graph_builder.discovery.change_detector import ChangeDetector
from app.core.parser.graph_builder.discovery.scanner import FileScanner
from app.core.services.file_service import FileService
from tests.unit.parser.analyzer.hierarchy.conftest import _build_and_get_tree


@pytest.mark.asyncio
async def test_new_folder_file_detection(setup_structure_project):
    project_node, repos, db_client, project_path = setup_structure_project

    file_scanner = FileScanner(
        project_path,
        ignore_file_name="",
    )
    scan_result = file_scanner.scan()

    change_detector = ChangeDetector(repos, DriverManager(Path(project_path)))
    change_set = await change_detector.detect_changes(scan_result)

    assert len(change_set.new_folders) == 3
    assert len(change_set.new_files) == 9
    assert len(change_set.deleted_folders) == 0
    assert len(change_set.deleted_files) == 0
    assert len(change_set.moved_folders) == 0
    assert len(change_set.moved_files) == 0
    assert len(change_set.modified_folders) == 0
    assert len(change_set.modified_files) == 0


@pytest.mark.asyncio
async def test_deleted_folder_file_detection(setup_structure_project):
    project_node, repos, db_client, project_path = setup_structure_project
    tree = await _build_and_get_tree(project_node, repos, db_client)
    assert tree is not None, "No tree nodes built"

    # Delete a folder
    file_scanner = FileScanner(
        project_path,
        ignore_file_name="",
    )
    scan_result = file_scanner.scan()

    change_detector = ChangeDetector(repos, DriverManager(Path(project_path)))
    change_set = await change_detector.detect_changes(scan_result)
    assert not change_set.has_changes()

    shutil.rmtree(project_path / "app")

    # Resync and get updated tree
    file_scanner = FileScanner(
        project_path,
        ignore_file_name="",
    )
    scan_result = file_scanner.scan()

    change_detector = ChangeDetector(repos, DriverManager(Path(project_path)))
    change_set = await change_detector.detect_changes(scan_result)
    assert change_set.has_changes()

    assert len(change_set.deleted_folders) == 1
    assert len(change_set.deleted_files) == 2

    assert "app" in change_set.deleted_folders[0].path
    assert "app/__init__.py" in change_set.deleted_files[0].path
    assert "app/api.py" in change_set.deleted_files[1].path

    print("change_set --- \n\n", change_set)


@pytest.mark.asyncio
async def test_modified_folder_file_detection(setup_structure_project):
    project_node, repos, db_client, project_path = setup_structure_project
    tree = await _build_and_get_tree(project_node, repos, db_client)
    assert tree is not None, "No tree nodes built"
    api_py = (project_path / "app" / "api.py")

    with open(api_py, "+a") as f:
        f.write("\nprint('Hello, World!')")

    # Modify a folder
    file_scanner = FileScanner(
        project_path,
        ignore_file_name="",
    )
    scan_result = file_scanner.scan()

    change_detector = ChangeDetector(repos, DriverManager(Path(project_path)))
    change_set = await change_detector.detect_changes(scan_result)

    assert change_set.has_changes()

    assert len(change_set.modified_files) == 1
    assert "app/api.py" in change_set.modified_files[0].path

    assert len(change_set.modified_folders) == 0
    assert len(change_set.deleted_folders) == 0
    assert len(change_set.deleted_files) == 0
    assert len(change_set.moved_folders) == 0
    assert len(change_set.moved_files) == 0


@pytest.mark.asyncio
async def test_folder_rename_detection(setup_structure_project):
    project_node, repos, db_client, project_path = setup_structure_project
    tree = await _build_and_get_tree(project_node, repos, db_client)
    assert tree is not None, "No tree nodes built"

    shutil.move(project_path / "app", project_path / "app2")

    # Move a folder
    file_scanner = FileScanner(
        project_path,
        ignore_file_name="",
    )
    scan_result = file_scanner.scan()

    change_detector = ChangeDetector(repos, DriverManager(Path(project_path)))
    change_set = await change_detector.detect_changes(scan_result)

    assert change_set.has_changes()

    assert len(change_set.modified_folders) == 1
    assert len(change_set.modified_files) == 2

    assert len(change_set.moved_folders) == 0
    assert len(change_set.moved_files) == 0
    assert len(change_set.deleted_folders) == 0
    assert len(change_set.deleted_files) == 0
    assert len(change_set.new_folders) == 0
    assert len(change_set.new_files) == 0


@pytest.mark.asyncio
async def test_folder_move_detection(setup_structure_project):
    project_node, repos, db_client, project_path = setup_structure_project
    tree = await _build_and_get_tree(project_node, repos, db_client)
    assert tree is not None, "No tree nodes built"

    shutil.move(project_path / "app"/"api.py", project_path / "api.py")

    # Move a folder
    file_scanner = FileScanner(
        project_path,
        ignore_file_name="",
    )
    scan_result = file_scanner.scan()

    change_detector = ChangeDetector(repos, DriverManager(Path(project_path)))
    change_set = await change_detector.detect_changes(scan_result)

    assert change_set.has_changes()
    assert len(change_set.modified_files) == 0
    assert len(change_set.modified_folders) == 0
    assert len(change_set.deleted_folders) == 0
    assert len(change_set.deleted_files) == 0
    assert len(change_set.moved_folders) == 0
    assert len(change_set.moved_files) == 1
    assert len(change_set.new_folders) == 0
    assert len(change_set.new_files) == 0

    shutil.move(project_path / "app", project_path / "core")

    file_scanner = FileScanner(
        project_path,
        ignore_file_name="",
    )
    scan_result = file_scanner.scan()

    change_detector = ChangeDetector(repos, DriverManager(Path(project_path)))
    change_set = await change_detector.detect_changes(scan_result)

    assert change_set.has_changes()
    assert len(change_set.moved_folders) == 1
