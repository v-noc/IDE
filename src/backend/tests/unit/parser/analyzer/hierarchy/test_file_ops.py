import pytest
import shutil
import asyncio


async def run_sync(ctx):
    scan_result = ctx["scanner"].scan()
    change_set = await ctx["change_detector"].detect_changes(scan_result)

    # Run structure sync (Folders + File Shells)
    folder_changes = await ctx["collector"].sync_structure(change_set, scan_result)

    return change_set


@pytest.mark.asyncio
async def test_file_add(synced_project):
    ctx = synced_project
    project_path = ctx["project_path"]
    repos = ctx["repos"]
    project_name = ctx["project_name"]

    new_file = project_path / "new_file.py"
    new_file.write_text("# new file")

    change_set = await run_sync(ctx)

    assert any(f.path == str(new_file) for f in change_set.new_files)

    node = await repos.nodes.find_by_qname(f"{project_name}.new_file")
    assert node is not None
    assert node.node_type == "file"


@pytest.mark.asyncio
async def test_file_remove(synced_project):
    ctx = synced_project
    project_path = ctx["project_path"]
    repos = ctx["repos"]
    project_name = ctx["project_name"]

    target = project_path / "main.py"

    node_before = await repos.nodes.find_by_qname(f"{project_name}.main")
    assert node_before

    target.unlink()

    change_set = await run_sync(ctx)

    assert any(f.path == str(target) for f in change_set.deleted_files)

    node_after = await repos.nodes.find_by_qname(f"{project_name}.main")
    assert node_after is None


@pytest.mark.asyncio
async def test_file_move(synced_project):
    ctx = synced_project
    project_path = ctx["project_path"]
    repos = ctx["repos"]
    project_name = ctx["project_name"]

    # Move "main.py" -> "core/main.py"
    src = project_path / "main.py"
    dst = project_path / "core" / "main.py"

    # Ensure dst folder exists (it does in fixture)

    node_before = await repos.nodes.find_by_qname(f"{project_name}.main")
    assert node_before
    # stable_id should be the key (UUID) to match MoveEvent.id
    stable_id = node_before.key if node_before.key else node_before.id.split(
        "/")[-1]

    old_parent = await repos.nodes.find_by_qname(project_name)
    assert old_parent is not None
    new_parent = await repos.nodes.find_by_qname(f"{project_name}.core")
    assert new_parent is not None

    shutil.move(src, dst)

    change_set = await run_sync(ctx)
    moved_files = change_set.moved_files

    assert any(m.id == stable_id for m in moved_files)

    # Check old gone
    assert await repos.nodes.find_by_qname(f"{project_name}.main") is None

    # Check new exists
    node_new = await repos.nodes.find_by_qname(f"{project_name}.core.main")
    assert node_new is not None
    node_new_key = node_new.key if node_new.key else node_new.id.split("/")[-1]
    assert node_new_key == stable_id

    # Parent relink check
    # Note: get_children returns raw dicts currently in NodeRepo
    old_children = await repos.nodes.get_children(old_parent.id)
    # Handle dict vs model
    old_child_ids = {c["_key"] if isinstance(
        c, dict) and "_key" in c else c.id for c in old_children}
    # ArangoDB IDs might be "collection/key".
    # If node.id is full ID, and c['_id'] is full ID, we compare those.
    # If node.id is key, we compare keys.
    # Usually node.id is set to _key in models for Arango.

    # Safest: compare full _id if available, or just keys.
    # Let's check what node.id is. Usually key.

    # Helper to get ID from child result
    def get_id(c):
        if isinstance(c, dict):
            # Depending on query, it might be the document.
            return c.get("_key")
        return c.key if c.key else c.id.split("/")[-1]

    assert stable_id not in {get_id(c) for c in old_children}

    new_children = await repos.nodes.get_children(new_parent.id)
    assert stable_id in {get_id(c) for c in new_children}


@pytest.mark.asyncio
async def test_file_rename(synced_project):
    ctx = synced_project
    project_path = ctx["project_path"]
    repos = ctx["repos"]
    project_name = ctx["project_name"]

    # "main.py" -> "entry.py"
    src = project_path / "main.py"
    dst = project_path / "entry.py"

    node_before = await repos.nodes.find_by_qname(f"{project_name}.main")
    stable_id = node_before.id
    root = await repos.nodes.find_by_qname(project_name)
    assert root is not None

    shutil.move(src, dst)

    await run_sync(ctx)

    node_new = await repos.nodes.find_by_qname(f"{project_name}.entry")
    assert node_new is not None
    assert node_new.id == stable_id

    # Parent link check
    root_children = await repos.nodes.get_children(root.id)

    def get_id(c):
        return c.get("_key") if isinstance(c, dict) else c.id

    def get_qname(c):
        return c.get("qname") if isinstance(c, dict) else c.qname

    child_ids = {f"nodes/{get_id(c)}" for c in root_children}
    assert stable_id in child_ids

    child_qnames = {get_qname(c) for c in root_children}
    assert f"{project_name}.entry" in child_qnames
    assert f"{project_name}.main" not in child_qnames


@pytest.mark.asyncio
async def test_file_rename_and_move(synced_project):
    ctx = synced_project
    project_path = ctx["project_path"]
    repos = ctx["repos"]
    project_name = ctx["project_name"]

    # "main.py" -> "core/entry.py"
    src = project_path / "main.py"
    dst = project_path / "core" / "entry.py"

    node_before = await repos.nodes.find_by_qname(f"{project_name}.main")
    stable_id = node_before.id

    old_parent = await repos.nodes.find_by_qname(project_name)
    assert old_parent is not None
    new_parent = await repos.nodes.find_by_qname(f"{project_name}.core")
    assert new_parent is not None

    shutil.move(src, dst)

    await run_sync(ctx)

    node_new = await repos.nodes.find_by_qname(f"{project_name}.core.entry")
    assert node_new is not None
    assert node_new.id == stable_id

    # Parent relink check
    def get_id(c):
        return c.get("_key") if isinstance(c, dict) else c.id

    old_children = await repos.nodes.get_children(old_parent.id)
    assert stable_id not in {f"nodes/{get_id(c)}" for c in old_children}

    new_children = await repos.nodes.get_children(new_parent.id)
    assert stable_id in {f"nodes/{get_id(c)}" for c in new_children}
