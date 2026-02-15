
from app.core.services.call_service import CallService

from app.core.services.function_service import FunctionService
import pytest


@pytest.mark.asyncio
async def test_create_call(create_repos, create_function, create_project):
    call_service = CallService(create_repos, create_project)

    new_call = await call_service.create(
        "Test Call",
        "test_project.test_call",
        "This is a test call",
        create_function.id,
    )
    assert new_call is not None
    assert new_call.name == "Test Call"
    assert new_call.qname == "test_project.test_call"
    assert new_call.description == "This is a test call"

    await call_service.delete(new_call.id)


@pytest.mark.asyncio
async def test_get_call(call_service, create_call):
    new_call = await call_service.get(create_call.id)
    assert new_call is not None
    assert new_call.name == "Test Call"
    assert new_call.qname == "test_project.test_call"
    assert new_call.description == "This is test call"


@pytest.mark.asyncio
async def test_update_call(create_call, call_service):

    create_call.name = "Updated Call"
    create_call.description = "This is an updated call"
    new_call = await call_service.update(create_call)
    assert new_call is not None
    assert new_call.name == "Updated Call"
    assert new_call.description == "This is an updated call"


@pytest.mark.asyncio
async def test_delete_call(create_call, call_service):
    await call_service.delete(create_call.id)
    new_call = await call_service.get(create_call.id)
    assert new_call is None


@pytest.mark.asyncio
async def test_add_call_to_function(
    create_call, create_call2, create_function, create_function3, call_service, function_service
):
    await function_service.add_call(create_function.id, create_call.id)
    call3 = await call_service.create(
        "Test Call 3",
        "test_project.test_call3",
        "This is a test call 3",
        create_function3.id,
    )
    await call_service.add_call(create_call.id, call3.id)

    # 2) Add create_function as a call inside create_function3 and clone its call graph
    clone_entry = await call_service.create(
        "Fn as Call",
        "test_project.fn_as_call",
        "Function as call",

        create_function.id,
    )
    await function_service.add_call(create_function3.id, clone_entry.id)

    await container_service.clone_callee_call_graph(
        create_function.id, clone_entry.id)

    # 3) Assertions: cloned structure under clone_entry
    descendants = await call_service.get_children(clone_entry.id)
    # Immediate children of clone_entry
    immediate = [d for d in descendants if d.get(
        "parent_id") == clone_entry.id]
    assert len(immediate) == 1
    first_child = immediate[0]["vertex"]
    assert first_child["node_type"] in ("call", "group")

    # If a group was created by any rule, it should contain the call; else child is the call itself
    if first_child["node_type"] == "group":
        group_children = [
            d for d in descendants if d.get("parent_id") == first_child.get("_id")
        ]
        assert len(group_children) >= 1
        cloned_call = group_children[0]["vertex"]
    else:
        cloned_call = first_child

    # The cloned call (of original create_call) should have its own child (cloned call3)
    level2 = [d for d in descendants if d.get(
        "parent_id") == cloned_call.get("_id")]
    assert len(level2) == 1
    level2_vertex = level2[0]["vertex"]
    assert level2_vertex["node_type"] == "call"


@pytest.mark.asyncio
async def test_add_call_to_call(create_call, create_call2, call_service):

    await call_service.add_call(create_call.id, create_call2.id)
    calls = await call_service.get_children(create_call.id)
    assert len(calls) == 1
    assert calls[0].id == create_call2.id
    assert calls[0].target_function is not None


@pytest.mark.asyncio
async def test_find_upward_call_chain(create_sample_project, arangodb_client):
    from app.core.builder.tree_builder import TreeBuilder
    from app.core.repository import Repositories
    from app.core.services.project_service import ProjectService

    repos = Repositories(arangodb_client)
    proj_service = ProjectService(repos)
    project = await proj_service.get_all()
    assert project

    children = await proj_service.get_children(project[0].id)
    tree = TreeBuilder(children).build()

    def _find_node(nodes, name: str, node_type: str):
        for n in reversed(nodes):
            if getattr(n, "node_type", "") == node_type and n.name == name:
                return n
            res = _find_node(getattr(n, "children", []) or [], name, node_type)
            if res:
                return res
        return None

    build_call = _find_node(tree, "build", "call")
    assert build_call is not None

    call_service = CallService(repos)
    chain_info = await call_service.get_call_parent_chain(build_call.id)

    assert chain_info is not None
    data = chain_info[0]

    origin = data.get("origin")
    calls = data.get("calls", [])

    assert origin["name"] == "main"

    expected_calls = ["add", "build"]
    assert len(calls) >= len(expected_calls)

    # for i, call_info in enumerate(calls):
    #     assert call_info["call"]["name"] == expected_calls[i]
    #     assert call_info["target"] is not None
