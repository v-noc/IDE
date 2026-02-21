import pytest

from app.core.services import (
    ProjectService,
    GroupService,
    FolderService,
)
from app.core.builder.tree_builder import TreeBuilder
from app.core.services.group_service import GroupType
from app.core.model.schemas import StructureGroupSchema


@pytest.mark.asyncio
async def test_group_creation(create_repos, create_project,  create_file, create_file2, create_folder):
    group_service = GroupService(create_repos, create_project)
    folder_service = FolderService(create_repos, create_project)
    project_service = ProjectService(create_repos)

    await folder_service.move_batch([(create_file.id, create_folder.id, "file")])
    await group_service.create("Test Group", "Test Group", None, [(create_file2.id, "file")], GroupType.STRUCTURE)

    children = await project_service.get_children(create_project.db_name)

    tree = TreeBuilder(children).build()

    assert len(tree) == 2, "Expected 2 children in the tree"

    group_node = None
    for i in tree:
        if i.id.startswith(StructureGroupSchema.__name__):
            group_node = i
            break

    assert group_node is not None, "Group node not found"
    assert group_node.name == "Test Group"
    assert len(group_node.children) == 1
    assert group_node.children[0].id == create_file2.id

    await group_service.move_item(group_node.id, create_folder.id, "folder", GroupType.STRUCTURE)

    children = await project_service.get_children(create_project.db_name)
    tree = TreeBuilder(children).build()

    assert len(tree) == 1, "Expected 1 children in the tree"

    assert tree[0].id == group_node.id

    await group_service.delete(group_node.id, GroupType.STRUCTURE)

    children = await project_service.get_children(create_project.db_name)
    tree = TreeBuilder(children).build()

    assert len(tree) == 2, "Expected 2 children in the tree"
