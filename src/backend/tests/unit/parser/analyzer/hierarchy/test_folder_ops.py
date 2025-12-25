import pytest
import shutil
import asyncio


async def run_sync(ctx):
    scan_result = ctx["scanner"].scan()
    change_set = await ctx["change_detector"].detect_changes(scan_result)
    await ctx["collector"].sync_structure(change_set, scan_result)
    return change_set


@pytest.mark.asyncio
async def test_folder_add(synced_project):
    ctx = synced_project
    project_path = ctx["project_path"]
    manager = ctx["scope_manager"]

    new_folder = project_path / "new_folder"
    new_folder.mkdir()
    (new_folder / "dummy.py").write_text("")

    change_set = await run_sync(ctx)

    # Assert
    assert any(f.path == str(new_folder) for f in change_set.new_folders)

    scope = await manager.get_scope_by_qname(f"{ctx['project_name']}.new_folder")
    assert scope is not None
    assert scope.type.value == "folder"


@pytest.mark.asyncio
async def test_folder_remove(synced_project):
    ctx = synced_project
    project_path = ctx["project_path"]
    manager = ctx["scope_manager"]

    target = project_path / "core"

    scope_before = await manager.get_scope_by_qname(f"{ctx['project_name']}.core")
    assert scope_before

    shutil.rmtree(target)

    change_set = await run_sync(ctx)

    assert any(f.path == str(target) for f in change_set.deleted_folders)

    scope_after = await manager.get_scope_by_qname(f"{ctx['project_name']}.core")
    assert scope_after is None


@pytest.mark.asyncio
async def test_folder_move(synced_project):
    ctx = synced_project
    project_path = ctx["project_path"]
    manager = ctx["scope_manager"]

    # Move "core/data" to "app/data"
    src = project_path / "core" / "data"
    dst = project_path / "app" / "data"

    # Ensure src exists and has ID
    scope_before = await manager.get_scope_by_qname(f"{ctx['project_name']}.core.data")
    assert scope_before
    stable_id = scope_before.id
    old_parent = await manager.get_scope_by_qname(f"{ctx['project_name']}.core")
    assert old_parent is not None
    new_parent = await manager.get_scope_by_qname(f"{ctx['project_name']}.app")
    assert new_parent is not None

    shutil.move(src, dst)

    change_set = await run_sync(ctx)

    # Verify move detected
    assert any(m.id == stable_id for m in change_set.moved_folders)

    # Verify new location
    scope_new = await manager.get_scope_by_qname(f"{ctx['project_name']}.app.data")
    assert scope_new is not None
    assert scope_new.id == stable_id
    assert scope_new.file_path == str(dst)

    # Parent relink check: old parent should not contain it, new parent should
    old_children = await manager.get_children(old_parent.id)
    assert stable_id not in {c.id for c in old_children}
    new_children = await manager.get_children(new_parent.id)
    assert stable_id in {c.id for c in new_children}


@pytest.mark.asyncio
async def test_folder_rename(synced_project):
    ctx = synced_project
    project_path = ctx["project_path"]
    manager = ctx["scope_manager"]

    # Rename "core" -> "kernel"
    src = project_path / "core"
    dst = project_path / "kernel"

    scope_before = await manager.get_scope_by_qname(f"{ctx['project_name']}.core")
    stable_id = scope_before.id
    root = await manager.get_scope_by_qname(ctx["project_name"])
    assert root is not None

    shutil.move(src, dst)

    await run_sync(ctx)

    scope_new = await manager.get_scope_by_qname(f"{ctx['project_name']}.kernel")
    assert scope_new is not None
    assert scope_new.id == stable_id

    # Parent link check: root should contain kernel, and no longer contain core
    root_children = await manager.get_children(root.id)
    child_qnames = {c.qname for c in root_children}
    assert f"{ctx['project_name']}.kernel" in child_qnames
    assert f"{ctx['project_name']}.core" not in child_qnames


@pytest.mark.asyncio
async def test_folder_rename_and_move(synced_project):
    ctx = synced_project
    project_path = ctx["project_path"]
    manager = ctx["scope_manager"]

    # Move "core/data" -> "app/info"
    src = project_path / "core" / "data"
    dst = project_path / "app" / "info"

    scope_before = await manager.get_scope_by_qname(f"{ctx['project_name']}.core.data")
    stable_id = scope_before.id
    old_parent = await manager.get_scope_by_qname(f"{ctx['project_name']}.core")
    assert old_parent is not None
    new_parent = await manager.get_scope_by_qname(f"{ctx['project_name']}.app")
    assert new_parent is not None

    shutil.move(src, dst)

    await run_sync(ctx)

    scope_new = await manager.get_scope_by_qname(f"{ctx['project_name']}.app.info")
    assert scope_new is not None
    assert scope_new.id == stable_id

    # Parent relink check: old parent should not contain it, new parent should
    old_children = await manager.get_children(old_parent.id)
    assert stable_id not in {c.id for c in old_children}
    new_children = await manager.get_children(new_parent.id)
    assert stable_id in {c.id for c in new_children}
