import pytest

from app.core.services import (
    ProjectService,
    GroupService,
    FileService,
)
from app.core.builder.tree_builder import TreeBuilder
from app.core.services.group_service import GroupType
from app.core.model.schemas import CodeElementGroupSchema


@pytest.mark.asyncio
async def test_group_creation(project_uow, create_function, create_function2, create_file, create_class):
    group_service = GroupService(project_uow)
    file_service = FileService(project_uow)

    await file_service.move_batch([(create_function.id, create_file.id,  "function"),
                                   (create_class.id, create_file.id, "class"), (create_function2.id, create_class.id, "function")])

    await group_service.create("Test Group", "Test Group", create_file.id, [(create_function.id, "function")], GroupType.CODE_ELEMENT)

    children = await file_service.get_children(create_file.id)

    tree = TreeBuilder(children).build()

    assert len(tree) == 2, "Expected 2 children in the tree"

    group_node = None
    for i in tree:
        if i.id.startswith(CodeElementGroupSchema.__name__):
            group_node = i
            break

    assert group_node is not None, "Group node not found"
    assert group_node.name == "Test Group"
    assert len(group_node.children) == 1
    assert group_node.children[0].id == create_function.id

    await group_service.move_item(group_node.id, create_class.id, "class", GroupType.CODE_ELEMENT)

    children = await file_service.get_children(create_file.id)

    tree = TreeBuilder(children).build()

    assert len(tree) == 1, "Expected 1 children in the tree"

    await group_service.delete(group_node.id, GroupType.CODE_ELEMENT)

    children = await file_service.get_children(create_file.id)

    tree = TreeBuilder(children).build()

    for i in tree:
        assert i.id != group_node.id

    assert len(tree) == 2, "Expected 2 children in the tree"


@pytest.mark.asyncio
async def test_group_move_batch(project_uow, create_function, create_function2, create_file, create_class):
    group_service = GroupService(project_uow)
    file_service = FileService(project_uow)

    await file_service.move_batch([(create_function.id, create_file.id,  "function"),
                                   (create_class.id, create_file.id, "class"), (create_function2.id, create_class.id, "function")])

    created_group = await group_service.create("Test Group", "Test Group", create_file.id, [], GroupType.CODE_ELEMENT)

    children = await file_service.get_children(create_file.id)
    tree = TreeBuilder(children).build()

    assert len(tree) == 3, "Expected 1 children in the tree"

    await group_service.move_batch([(create_function.id, created_group.id, "function"), (create_class.id, created_group.id,
                                                                                         "class")], GroupType.CODE_ELEMENT)

    children = await file_service.get_children(create_file.id)
    tree = TreeBuilder(children).build()

    assert len(tree) == 1, "Expected 1 children in the tree"
    assert tree[0].id == created_group.id

    await file_service.move_batch([(create_function.id, create_file.id, "function"), (create_class.id, create_file.id, "class")])

    children = await file_service.get_children(create_file.id)
    tree = TreeBuilder(children).build()

    assert len(tree) == 3
