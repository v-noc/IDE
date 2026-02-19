
from app.core.services.call_service import CallService

from app.core.services.function_service import FunctionService
import pytest
from app.core.model.schemas.code_element_schema import CallSchema
from app.core.schemas.tree import CallTreeNode


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
    create_call,  create_function, create_function3, call_service, function_service
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
    await function_service.add_call(create_function.id, clone_entry.id)

    await call_service.add_call(
        create_function.id, clone_entry.id)

    # 3) Assertions: cloned structure under clone_entry
    descendants = await call_service.get_direct_call_children(create_function.id, CallSchema.__name__)
    for descendant in descendants:
        print(descendant["call"]["name"])
        print(descendant["target"])
    # Immediate children of clone_entry


@pytest.mark.asyncio
async def test_add_call_to_call(create_call, create_call2, call_service):

    await call_service.add_call(create_call.id, create_call2.id)
    calls = await call_service.get_children(create_call.id)
    assert len(calls) == 1
    assert calls[0].id == create_call2.id
    assert calls[0].target_function is not None


@pytest.mark.asyncio
async def test_find_upward_call_chain(create_sample_project, create_repos):
    project = create_sample_project
    from app.core.builder.tree_builder import TreeBuilder
    from app.core.services.project_service import ProjectService

    proj_service = ProjectService(create_repos)

    children = await proj_service.get_children(project.db_name)
    tree = TreeBuilder(children).build()

    def _find_node(nodes, name: str, node_type: str):
        for n in reversed(nodes):
            if n.__class__.__name__ == node_type and n.name == name:
                return n
            res = _find_node(getattr(n, "children", []) or [], name, node_type)
            if res:
                return res
        return None

    build_call = _find_node(tree, "build", CallTreeNode.__name__)
    assert build_call is not None

    call_service = CallService(create_repos, project)
    chain_info = await call_service.get_call_parent_chain(build_call.id)

    assert chain_info is not None
    print(chain_info)
    # data = chain_info[0]
    assert len(chain_info) > 2

    # origin = data.get("origin")
    # calls = data.get("calls", [])

    # assert origin["name"] == "main"

    # expected_calls = ["add", "build"]
    # assert len(calls) >= len(expected_calls)

    # for i, call_info in enumerate(calls):
    #     assert call_info["call"]["name"] == expected_calls[i]
    #     assert call_info["target"] is not None
