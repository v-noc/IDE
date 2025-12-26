import pytest
import shutil
import asyncio


async def run_sync(ctx):
    scan_result = ctx["scanner"].scan()
    change_set = await ctx["change_detector"].detect_changes(scan_result)
    await ctx["collector"].sync_structure(change_set, scan_result)

    # Handle File Deletions (Manual Repo Logic)
    if change_set.deleted_files:
        for tp in change_set.deleted_files:
            if tp.id:
                key = tp.id.split("/")[-1]
                await ctx["repos"].file_repo.delete(key)

    # Handle Folder Deletions (if any, though collector typically handles structure)
    if change_set.deleted_folders:
        for tp in change_set.deleted_folders:
            if tp.id:
                key = tp.id.split("/")[-1]
                await ctx["repos"].folder_repo.delete(key)

    return change_set


@pytest.mark.asyncio
async def test_folder_add(synced_project):
    ctx = synced_project
    project_path = ctx["project_path"]
    repos = ctx["repos"]
    project_name = ctx["project_name"]

    new_folder = project_path / "new_folder"
    new_folder.mkdir()
    (new_folder / "dummy.py").write_text("")

    change_set = await run_sync(ctx)

    # Assert
    assert any(f.path == str(new_folder) for f in change_set.new_folders)

    node = await repos.nodes.find_by_qname(f"{project_name}.new_folder")
    assert node is not None
    assert node.node_type == "folder"


@pytest.mark.asyncio
async def test_folder_remove(synced_project):
    ctx = synced_project
    project_path = ctx["project_path"]
    repos = ctx["repos"]
    project_name = ctx["project_name"]

    target = project_path / "core"

    node_before = await repos.nodes.find_by_qname(f"{project_name}.core")
    assert node_before

    shutil.rmtree(target)

    change_set = await run_sync(ctx)

    assert any(f.path == str(target) for f in change_set.deleted_folders)

    node_after = await repos.nodes.find_by_qname(f"{project_name}.core")
    assert node_after is None


@pytest.mark.asyncio
async def test_folder_move(synced_project):
    ctx = synced_project
    project_path = ctx["project_path"]
    repos = ctx["repos"]
    project_name = ctx["project_name"]

    # Move "core/data" to "app/data"
    src = project_path / "core" / "data"
    dst = project_path / "app" / "data"

    # Ensure src exists and has ID
    node_before = await repos.nodes.find_by_qname(f"{project_name}.core.data")
    assert node_before
    stable_id = node_before.id

    old_parent = await repos.nodes.find_by_qname(f"{project_name}.core")
    assert old_parent is not None
    new_parent = await repos.nodes.find_by_qname(f"{project_name}.app")
    assert new_parent is not None

    shutil.move(src, dst)

    change_set = await run_sync(ctx)

    # Verify move detected
    assert any(f"nodes/{m.id}" == stable_id for m in change_set.moved_folders)

    # Verify new location
    node_new = await repos.nodes.find_by_qname(f"{project_name}.app.data")
    assert node_new is not None
    assert node_new.id == stable_id
    assert node_new.path == str(dst)

    # Parent relink check
    def get_id(c):
        return c.get("_key") if isinstance(c, dict) else c.id

    old_children = await repos.nodes.get_children(old_parent.id)
    assert stable_id not in {f"nodes/{get_id(c)}" for c in old_children}

    new_children = await repos.nodes.get_children(new_parent.id)
    assert stable_id in {f"nodes/{get_id(c)}" for c in new_children}


@pytest.mark.asyncio
async def test_folder_rename(synced_project):
    ctx = synced_project
    project_path = ctx["project_path"]
    repos = ctx["repos"]
    project_name = ctx["project_name"]

    # Rename "core" -> "kernel"
    src = project_path / "core"
    dst = project_path / "kernel"

    node_before = await repos.nodes.find_by_qname(f"{project_name}.core")
    stable_id = node_before.id
    root = await repos.nodes.find_by_qname(project_name)
    assert root is not None

    shutil.move(src, dst)

    await run_sync(ctx)

    node_new = await repos.nodes.find_by_qname(f"{project_name}.kernel")
    assert node_new is not None
    assert node_new.id == stable_id

    # Parent link check
    def get_qname(c):
        return c.get("qname") if isinstance(c, dict) else c.qname

    root_children = await repos.nodes.get_children(root.id)
    child_qnames = {get_qname(c) for c in root_children}
    assert f"{project_name}.kernel" in child_qnames
    assert f"{project_name}.core" not in child_qnames


@pytest.mark.asyncio
async def test_folder_rename_and_move(synced_project):
    ctx = synced_project
    project_path = ctx["project_path"]
    repos = ctx["repos"]
    project_name = ctx["project_name"]

    # Move "core/data" -> "app/info"
    src = project_path / "core" / "data"
    dst = project_path / "app" / "info"

    node_before = await repos.nodes.find_by_qname(f"{project_name}.core.data")
    stable_id = node_before.id

    old_parent = await repos.nodes.find_by_qname(f"{project_name}.core")
    assert old_parent is not None
    new_parent = await repos.nodes.find_by_qname(f"{project_name}.app")
    assert new_parent is not None

    shutil.move(src, dst)

    await run_sync(ctx)

    node_new = await repos.nodes.find_by_qname(f"{project_name}.app.info")
    assert node_new is not None
    assert node_new.id == stable_id

    # Parent relink check
    def get_id(c):
        return c.get("_key") if isinstance(c, dict) else c.id

    old_children = await repos.nodes.get_children(old_parent.id)
    assert stable_id not in {f"nodes/{get_id(c)}" for c in old_children}

    new_children = await repos.nodes.get_children(new_parent.id)
    assert stable_id in {f"nodes/{get_id(c)}" for c in new_children}
