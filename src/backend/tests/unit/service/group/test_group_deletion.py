import pytest
from app.core.services import (
    ProjectService,
    GroupService,
    FileService,
)
from app.core.builder.tree_builder import TreeBuilder


@pytest.mark.asyncio
async def test_group_deletion_with_children(create_repos):
    project_service = ProjectService(create_repos)
    group_service = GroupService(create_repos)
    file_service = FileService(create_repos)

    project = await project_service.create("Test Project", "Test Project", "test_project")

    f1 = await file_service.create("File 1", "file_1", "File 1", "file1.py", "file1.py")
    f2 = await file_service.create("File 2", "file_2", "File 2", "file2.py", "file2.py")

    await project_service.add_file(project.id, f1.id)
    await project_service.add_file(project.id, f2.id)

    # Group the two files under the project
    group = await group_service.create("G", "G", project.key, [f1.key, f2.key])

    children = await project_service.get_children(project.id)
    tree = TreeBuilder(children).build()
    grp = next((n for n in tree if n.node_type == "group"), None)
    assert grp is not None and len(grp.children) == 2

    # Delete group while removing child edges explicitly
    ok = await group_service.delete(group.id, remove_children=True)
    assert ok is True

    # Group should be gone; its former children should not appear
    children = await project_service.get_children(project.id)
    tree = TreeBuilder(children).build()
    assert next((n for n in tree if n.node_type == "group"), None) is None
    assert next((n for n in tree if n.id in (f1.id, f2.id)), None) is None


@pytest.mark.asyncio
async def test_group_deletion_without_children(create_repos):
    project_service = ProjectService(create_repos)
    group_service = GroupService(create_repos)
    file_service = FileService(create_repos)

    project = await project_service.create("Test Project", "Test Project", "test_project")

    f1 = await file_service.create("File 1", "file_1", "File 1", "file1.py", "file1.py")
    f2 = await file_service.create("File 2", "file_2", "File 2", "file2.py", "file2.py")

    await project_service.add_file(project.id, f1.id)
    await project_service.add_file(project.id, f2.id)

    # Group the two files under the project
    group = await group_service.create("G", "G", project.key, [f1.key, f2.key])

    children = await project_service.get_children(project.id)
    tree = TreeBuilder(children).build()
    grp = next((n for n in tree if n.node_type == "group"), None)
    assert grp is not None and len(grp.children) == 2

    # Delete group without removing child edges first
    ok = await group_service.delete(group.id, remove_children=False)
    assert ok is True

    # Group should be gone; its former children should not appear
    children = await project_service.get_children(project.id)
    tree = TreeBuilder(children).build()
    assert next((n for n in tree if n.node_type == "group"), None) is None
    assert next((n for n in tree if n.id in (f1.id, f2.id)), None) is not None
