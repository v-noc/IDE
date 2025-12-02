from app.core.model.properties import CodePosition
from app.core.services.call_service import CallService
from app.core.services.container_service import ContainerService
from app.core.services.function_service import FunctionService


def test_create_call(create_repos, create_function):
    call_service = CallService(create_repos)
    position = CodePosition(line_no=1, col_offset=0,
                            end_line_no=1, end_col_offset=0)
    new_call = call_service.create(
        "Test Call",
        "test_project.test_call",
        "This is a test call",
        position,
        create_function.id,
    )
    assert new_call is not None
    assert new_call.name == "Test Call"
    assert new_call.qname == "test_project.test_call"
    assert new_call.description == "This is a test call"


def test_get_call(create_repos, create_call):
    call_service = CallService(create_repos)
    new_call = call_service.get(create_call.id)
    assert new_call is not None
    assert new_call.name == "Test Call"
    assert new_call.qname == "test_project.test_call"
    assert new_call.description == "This is test call"


def test_update_call(create_repos, create_call):
    call_service = CallService(create_repos)
    create_call.name = "Updated Call"
    create_call.description = "This is an updated call"
    new_call = call_service.update(create_call)
    assert new_call is not None
    assert new_call.name == "Updated Call"
    assert new_call.description == "This is an updated call"


def test_delete_call(create_repos, create_call):
    call_service = CallService(create_repos)
    call_service.delete(create_call.id)
    new_call = call_service.get(create_call.id)
    assert new_call is None


def test_add_call_to_function(
    create_repos, create_function, create_function3, create_call, create_call2
):
    call_service = CallService(create_repos)
    function_service = FunctionService(create_repos)
    container_service = ContainerService(create_repos)

    # 1) Construct chain: create_function -> create_call -> create_call3
    # Ensure the first call is attached under the function
    function_service.add_call(create_function.id, create_call.id)

    # Create call3 that targets function3 and attach under create_call
    position = CodePosition(line_no=1, col_offset=0,
                            end_line_no=1, end_col_offset=0)
    call3 = call_service.create(
        "Test Call 3",
        "test_project.test_call3",
        "This is a test call 3",
        position,
        create_function3.id,
    )
    call_service.add_call(create_call.id, call3.id)

    # 2) Add create_function as a call inside create_function3 and clone its call graph
    clone_entry = call_service.create(
        "Fn as Call",
        "test_project.fn_as_call",
        "Function as call",
        position,
        create_function.id,
    )
    function_service.add_call(create_function3.id, clone_entry.id)
    container_service.clone_callee_call_graph(
        create_function.id, clone_entry.id)

    # 3) Assertions: cloned structure under clone_entry
    descendants = call_service.get_children(clone_entry.id)
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


def test_add_call_to_call(create_repos, create_call, create_call2):
    call_service = CallService(create_repos)
    call_service.add_call(create_call.id, create_call2.id)
    calls = call_service.get_children(create_call.id)
    assert len(calls) == 1
    assert calls[0]["vertex"]["_id"] == create_call2.id
    assert calls[0]["target"] is not None


def test_find_upward_call_chain(create_sample_project, arangodb_client):
    from app.core.builder.tree_builder import TreeBuilder
    from app.core.repository import Repositories
    from app.core.services.project_service import ProjectService

    repos = Repositories(arangodb_client)
    proj_service = ProjectService(repos)
    project = proj_service.get_all()
    assert project

    children = proj_service.get_children(project[0].id)
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
    chain_info = call_service.get_call_parent_chain(build_call.id)

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
