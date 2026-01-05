import pytest
from pathlib import Path


@pytest.mark.asyncio
async def test_hierarchy_and_ignore(synced_project):
    """
    Test that the initial hierarchy is built correctly and respects ignore files.
    """
    ctx = synced_project
    project_path = ctx["project_path"]
    repos = ctx["repos"]
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

    for f in expected_files:
        assert f in scanned_paths, f"File {f} not found in scan result"

    # Check ignored
    assert "build/ignored.py" not in scanned_paths

    # Check DB Scopes
    project_name = ctx["project_name"]

    root = await repos.nodes.find_by_qname(project_name)
    # ProjectNode is type folder usually, or project? Check ProjectNode.
    assert root and root.node_type == "project"

    main = await repos.nodes.find_by_qname(f"{project_name}.main")
    assert main and main.node_type == "file"

    core = await repos.nodes.find_by_qname(f"{project_name}.core")
    assert core and core.node_type == "folder"

    core_data = await repos.nodes.find_by_qname(f"{project_name}.core.data")
    assert core_data and core_data.node_type == "folder"


@pytest.mark.asyncio
async def test_scope_contains_links(synced_project):
    """
    Test that parent-child relationships are correctly established.
    """
    ctx = synced_project
    repos = ctx["repos"]
    project_name = ctx["project_name"]

    root = await repos.nodes.find_by_qname(project_name)
    assert root

    # Check root children
    # Handle NodeRepo returning dicts
    def get_name(c):
        return c.get("name") if isinstance(c, dict) else c.name

    children = await repos.nodes.get_children(root.id)
    child_names = {get_name(c) for c in children}
    assert "main" in child_names
    assert "core" in child_names
    assert "app" in child_names

    # Check core children
    core = await repos.nodes.find_by_qname(f"{project_name}.core")
    core_children = await repos.nodes.get_children(core.id)
    core_names = {get_name(c) for c in core_children}
    assert "user" in core_names
    assert "post" in core_names
    assert "data" in core_names
