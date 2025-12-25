import pytest
import shutil
import asyncio


async def run_sync(ctx):
    scan_result = ctx["scanner"].scan()
    change_set = await ctx["change_detector"].detect_changes(scan_result)

    # Run structure sync (Folders + File Shells)
    folder_changes = await ctx["collector"].sync_structure(change_set, scan_result)

    # Handle File Deletions (Orchestrator logic)
    if change_set.deleted_files:
        await ctx["deletion_handler"].handle_batch_file_deletions(
            [tp.path for tp in change_set.deleted_files if tp.path],
            folder_changes,
            set()  # touched_folder_ids
        )

    return change_set


@pytest.mark.asyncio
async def test_file_add(synced_project):
    ctx = synced_project
    project_path = ctx["project_path"]
    manager = ctx["scope_manager"]

    new_file = project_path / "new_file.py"
    new_file.write_text("# new file")

    change_set = await run_sync(ctx)

    assert any(f.path == str(new_file) for f in change_set.new_files)

    scope = await manager.get_scope_by_qname(f"{ctx['project_name']}.new_file")
    assert scope is not None
    assert scope.type.value == "file"


@pytest.mark.asyncio
async def test_file_remove(synced_project):
    ctx = synced_project
    project_path = ctx["project_path"]
    manager = ctx["scope_manager"]

    target = project_path / "main.py"

    scope_before = await manager.get_scope_by_qname(f"{ctx['project_name']}.main")
    assert scope_before

    target.unlink()

    change_set = await run_sync(ctx)

    assert any(f.path == str(target) for f in change_set.deleted_files)

    scope_after = await manager.get_scope_by_qname(f"{ctx['project_name']}.main")
    assert scope_after is None


@pytest.mark.asyncio
async def test_file_move(synced_project):
    ctx = synced_project
    project_path = ctx["project_path"]
    manager = ctx["scope_manager"]

    # Move "main.py" -> "core/main.py"
    src = project_path / "main.py"
    dst = project_path / "core" / "main.py"

    # Ensure dst folder exists (it does in fixture)

    scope_before = await manager.get_scope_by_qname(f"{ctx['project_name']}.main")
    stable_id = scope_before.id
    old_parent = await manager.get_scope_by_qname(ctx["project_name"])
    assert old_parent is not None
    new_parent = await manager.get_scope_by_qname(f"{ctx['project_name']}.core")
    assert new_parent is not None

    shutil.move(src, dst)

    change_set = await run_sync(ctx)

    assert any(m.id == stable_id for m in change_set.moved_files)

    # Check old gone
    assert await manager.get_scope_by_qname(f"{ctx['project_name']}.main") is None

    # Check new exists
    scope_new = await manager.get_scope_by_qname(f"{ctx['project_name']}.core.main")
    assert scope_new is not None
    assert scope_new.id == stable_id

    # Parent relink check: root should not contain it; core should contain it
    old_children = await manager.get_children(old_parent.id)
    assert stable_id not in {c.id for c in old_children}
    new_children = await manager.get_children(new_parent.id)
    assert stable_id in {c.id for c in new_children}


@pytest.mark.asyncio
async def test_file_rename(synced_project):
    ctx = synced_project
    project_path = ctx["project_path"]
    manager = ctx["scope_manager"]

    # "main.py" -> "entry.py"
    src = project_path / "main.py"
    dst = project_path / "entry.py"

    scope_before = await manager.get_scope_by_qname(f"{ctx['project_name']}.main")
    stable_id = scope_before.id
    root = await manager.get_scope_by_qname(ctx["project_name"])
    assert root is not None

    shutil.move(src, dst)

    await run_sync(ctx)

    scope_new = await manager.get_scope_by_qname(f"{ctx['project_name']}.entry")
    assert scope_new is not None
    assert scope_new.id == stable_id

    # Parent link check: root should now contain entry, not main
    root_children = await manager.get_children(root.id)
    child_ids = {c.id for c in root_children}
    assert stable_id in child_ids
    child_qnames = {c.qname for c in root_children}
    assert f"{ctx['project_name']}.entry" in child_qnames
    assert f"{ctx['project_name']}.main" not in child_qnames


@pytest.mark.asyncio
async def test_file_rename_and_move(synced_project):
    ctx = synced_project
    project_path = ctx["project_path"]
    manager = ctx["scope_manager"]

    # "main.py" -> "core/entry.py"
    src = project_path / "main.py"
    dst = project_path / "core" / "entry.py"

    scope_before = await manager.get_scope_by_qname(f"{ctx['project_name']}.main")
    stable_id = scope_before.id
    old_parent = await manager.get_scope_by_qname(ctx["project_name"])
    assert old_parent is not None
    new_parent = await manager.get_scope_by_qname(f"{ctx['project_name']}.core")
    assert new_parent is not None

    shutil.move(src, dst)

    await run_sync(ctx)

    scope_new = await manager.get_scope_by_qname(f"{ctx['project_name']}.core.entry")
    assert scope_new is not None
    assert scope_new.id == stable_id

    # Parent relink check: root should not contain it; core should contain it
    old_children = await manager.get_children(old_parent.id)
    assert stable_id not in {c.id for c in old_children}
    new_children = await manager.get_children(new_parent.id)
    assert stable_id in {c.id for c in new_children}
