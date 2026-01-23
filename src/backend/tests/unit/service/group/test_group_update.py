import pytest
from app.core.services import (
    ProjectService,
    GroupService,
    FileService,
)
from app.core.builder.tree_builder import TreeBuilder

@pytest.mark.asyncio
async def test_group_add_child(create_repos):
    # add 1 child to group
    project_service = ProjectService(create_repos)
    group_service = GroupService(create_repos)
    file_service = FileService(create_repos)

    project = await project_service.create("Test Project", "Test Project", "test_project")

    f1 = await file_service.create("File 1", "file_1", "File 1", "file1.py", "file1.py")
    f2 = await file_service.create("File 2", "file_2", "File 2", "file2.py", "file2.py")

    await project_service.add_file(project.id, f1.id)
    await project_service.add_file(project.id, f2.id)

    # Create group with one default child (f1)
    group = await group_service.create("G", "G", project.key, [f1.key])

    # Initially, project has group and remaining file f2
    children = await project_service.get_children(project.id)
    tree = TreeBuilder(children).build()
    assert len(tree) == 2

    # Move f2 into the group: remove edge from project, then add to group
    await group_service.add_child_to_group(group.id, f2.id)

    # Now project should only have the group
    children = await project_service.get_children(project.id)
    tree = TreeBuilder(children).build()
    assert len(tree) == 1
    grp = next((n for n in tree if n.node_type == "group"), None)
    assert grp is not None and len(grp.children) == 2


@pytest.mark.asyncio
async def test_group_remove_child(create_repos):
    # remove 1 child from group
    project_service = ProjectService(create_repos)
    group_service = GroupService(create_repos)
    file_service = FileService(create_repos)

    project = await project_service.create("Test Project", "Test Project", "test_project")

    f1 = await file_service.create("File 1", "file_1", "File 1", "file1.py", "file1.py")
    f2 = await file_service.create("File 2", "file_2", "File 2", "file2.py", "file2.py")

    await project_service.add_file(project.id, f1.id)
    await project_service.add_file(project.id, f2.id)

    # Create group with both children
    group = await group_service.create("G", "G", project.key, [f1.key, f2.key])

    children = await project_service.get_children(project.id)
    tree = TreeBuilder(children).build()
    grp = next((n for n in tree if n.node_type == "group"), None)
    assert grp is not None and len(grp.children) == 2

    # Remove one child (f2) from group
    ok = await group_service.remove_child_from_group(group.id, f2.id)
    assert ok is True

    # Project still only shows the group; the removed child is orphaned
    children = await project_service.get_children(project.id)
    tree = TreeBuilder(children).build()
    grp = next((n for n in tree if n.node_type == "group"), None)
    assert grp is not None and len(grp.children) == 1
    assert len(tree) == 2


@pytest.mark.asyncio
async def test_group_update_information(create_repos):
    # update name, description, and icon
    project_service = ProjectService(create_repos)
    group_service = GroupService(create_repos)
    file_service = FileService(create_repos)

    project = await project_service.create("Test Project", "Test Project", "test_project")

    f1 = await file_service.create("File 1", "file_1", "File 1", "file1.py", "file1.py")
    await project_service.add_file(project.id, f1.id)

    group = await group_service.create("G", "G", project.key, [f1.key])

    updated = await group_service.update_basic_info(
        group.id,
        name="New Name",
        description="New Description",
        icon="new-icon",
    )
    assert updated is not None

    fetched = await group_service.get(group.id)
    assert fetched is not None
    assert fetched.name == "New Name"
    assert fetched.description == "New Description"
    assert getattr(fetched, "icon", None) == "new-icon"
