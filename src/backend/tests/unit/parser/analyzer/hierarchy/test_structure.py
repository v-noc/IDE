import pytest
from pathlib import Path


@pytest.mark.asyncio
async def test_hierarchy_and_ignore(synced_project):
    """
    Test that the initial hierarchy is built correctly and respects ignore files.
    """
    ctx = synced_project
    project_path = ctx["project_path"]
    manager = ctx["scope_manager"]
    scan_result = ctx["scanner"].scan()

    scanned_paths = {
        Path(p).relative_to(project_path).as_posix()
        for p in scan_result.files.keys()
    }

    # Files that should exist
    expected_files = {
        "main.py",
        "core/user.py",
        "core/post.py",
        "core/data/user.py",
        "app/api.py",
    }

    # Assuming the simple_project fixture matches these expectations
    # If fixture is missing files, this might fail, but based on original test it should pass
    # We check if expected files are present
    for f in expected_files:
        assert f in scanned_paths, f"File {f} not found in scan result"

    # Check ignored
    assert "build/ignored.py" not in scanned_paths

    # Check DB Scopes
    project_name = ctx["project_name"]

    root = await manager.get_scope_by_qname(project_name)
    assert root and root.type.value == "folder"

    main = await manager.get_scope_by_qname(f"{project_name}.main")
    assert main and main.type.value == "file"

    core = await manager.get_scope_by_qname(f"{project_name}.core")
    assert core and core.type.value == "folder"

    core_data = await manager.get_scope_by_qname(f"{project_name}.core.data")
    assert core_data and core_data.type.value == "folder"


@pytest.mark.asyncio
async def test_scope_contains_links(synced_project):
    """
    Test that parent-child relationships are correctly established.
    """
    ctx = synced_project
    manager = ctx["scope_manager"]
    project_name = ctx["project_name"]

    root = await manager.get_scope_by_qname(project_name)
    assert root

    # Check root children
    children = await manager.get_children(root.id)
    child_names = {c.name for c in children}
    assert "main" in child_names
    assert "core" in child_names
    assert "app" in child_names

    # Check core children
    core = await manager.get_scope_by_qname(f"{project_name}.core")
    core_children = await manager.get_children(core.id)
    core_names = {c.name for c in core_children}
    assert "user" in core_names
    assert "post" in core_names
    assert "data" in core_names
