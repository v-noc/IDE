import pytest

from app.core.services import (
    GroupService,
    FunctionService,
    CallService,
)
from app.core.builder.tree_builder import TreeBuilder
from app.core.services.group_service import GroupType
from app.core.model.schemas import CallGroupSchema


@pytest.mark.asyncio
async def test_call_group_creation(
    create_repos,
    create_project,
    create_function,
    create_function2,
    create_call,
    create_call2,
):
    group_service = GroupService(create_repos, create_project)
    function_service = FunctionService(create_repos, create_project)
    call_service = CallService(create_repos, create_project)

    await function_service.add_call(create_function.id, create_call.id)
    await function_service.add_call(create_function.id, create_call2.id)

    await group_service.create(
        "Test Call Group",
        "Test Call Group",
        create_function.id,
        [(create_call.id, "call")],
        GroupType.CALL,
    )

    children = await function_service.get_children(create_function.id)
    tree = TreeBuilder(children).build()

    assert len(tree) == 1, "Expected 1 root (the function)"
    func_node = tree[0]
    assert len(func_node.children) >= 1, "Expected at least 1 child (call_group)"

    group_node = None
    for child in func_node.children:
        if child.id.startswith(CallGroupSchema.__name__):
            group_node = child
            break

    assert group_node is not None, "Call group node not found"
    assert group_node.name == "Test Call Group"
    assert len(group_node.children) == 1
    assert group_node.children[0].id == create_call.id

    await group_service.move_item(
        group_node.id, create_call2.id, "call", GroupType.CALL
    )

    children = await function_service.get_children(create_function.id)
    tree = TreeBuilder(children).build()

    group_node = None
    for child in tree[0].children:
        if child.id.startswith(CallGroupSchema.__name__):
            group_node = child
            break

    assert group_node is not None
    assert len(group_node.children) == 2

    await group_service.delete(group_node.id, GroupType.CALL)

    children = await function_service.get_children(create_function.id)
    tree = TreeBuilder(children).build()

    for child in tree[0].children:
        assert not child.id.startswith(CallGroupSchema.__name__)

    assert len(tree[0].children) == 2, "Expected 2 calls back under function"


@pytest.mark.asyncio
async def test_call_group_move_batch(
    create_repos,
    create_project,
    create_function,
    create_function2,
    create_call,
    create_call2,
):
    group_service = GroupService(create_repos, create_project)
    function_service = FunctionService(create_repos, create_project)

    await function_service.add_call(create_function.id, create_call.id)
    await function_service.add_call(create_function.id, create_call2.id)

    created_group = await group_service.create(
        "Test Call Group",
        "Test Call Group",
        create_function.id,
        [],
        GroupType.CALL,
    )

    children = await function_service.get_children(create_function.id)
    tree = TreeBuilder(children).build()

    assert len(tree[0].children) == 3, "Expected 3 children (2 calls + 1 group)"

    await group_service.move_batch(
        [
            (create_call.id, created_group.id, "call"),
            (create_call2.id, created_group.id, "call"),
        ],
        GroupType.CALL,
    )

    children = await function_service.get_children(create_function.id)
    tree = TreeBuilder(children).build()

    assert len(tree[0].children) == 1, "Expected 1 child (the group)"
    assert tree[0].children[0].id == created_group.id
    assert len(tree[0].children[0].children) == 2

    await create_repos.function_repo.move_batch(
        [
            (create_call.id, create_function.id, "call"),
            (create_call2.id, create_function.id, "call"),
        ],
        create_project.db_name,
    )

    children = await function_service.get_children(create_function.id)
    tree = TreeBuilder(children).build()

    assert len(tree[0].children) == 3
