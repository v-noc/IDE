from vn_logger import configure_logger, stop_worker_thread, context_logger, logger
import pytest
from app.core.services.project_service import ProjectService
from app.db.context import RequestDbContext, ProjectUoW
from app.core.services.log_service import LogService


def _find_fn(nodes, name: str):
    for n in nodes:
        if getattr(n, "node_type", "") == "function" and n.name == name:
            return n
        res = _find_fn(getattr(n, "children", []) or [], name)
        if res:
            return res
    return None


@pytest.mark.asyncio
async def test_vn_logger(jsonrpc_url, create_sample_project, terminusdb_client):
    # Use real server URL; worker will use requests.post
    project_node = create_sample_project
    ctx = RequestDbContext()
    project_uow = ProjectUoW(terminusdb_client, project_node, ctx)

    proj_service = ProjectService(project_uow)
    log_service = LogService(project_uow)

    project_id = project_node.id

    from app.core.builder.tree_builder import TreeBuilder

    children = await proj_service.get_children()
    tree = TreeBuilder(children).build()
    factory_fn = _find_fn(tree, "factory")
    add_fn = _find_fn(tree, "add")
    build_fn = _find_fn(tree, "build")
    assert factory_fn and add_fn and build_fn
    configure_logger(
        jsonrpc_url,
        project_id,
    )

    @context_logger(function_id=build_fn.id.split("/")[-1])
    def build_function(param: str):
        logger.info("build_function ")
        return {"value": "test"}

    @context_logger(function_id=add_fn.id.split("/")[-1])
    def add_function(pp):
        build_function("test")
        return {"value": "test"}

    add_function("dad")
    # Ensure background thread shuts down cleanly
    stop_worker_thread()

    add_log_tree = await log_service.get_function_log(add_fn.id)
    build_log_tree = await log_service.get_function_log(build_fn.id)

    assert len(add_log_tree) == 1
    assert len(build_log_tree) == 1

    add_log = add_log_tree[0]
    add_log_children = add_log.children

    assert len(add_log_children) == 2
    # Root add_function enter
    assert add_log.event_type == "enter"
    assert add_log.message.startswith("Enter")
    assert add_log.payload is not None
    assert add_log.payload.get("args") == ["'dad'"]
    assert add_log.payload.get("kwargs") == {}

    # Under add enter: children are build enter and add exit
    build_enter = next(
        (c for c in add_log_children if c.event_type == "enter"), None
    )
    add_exit = next(
        (c for c in add_log_children if c.event_type == "exit"), None
    )
    assert build_enter is not None and add_exit is not None

    assert build_enter.message.startswith("Enter")
    assert build_enter.payload is not None
    assert build_enter.payload.get("args") == ["'test'"]
    assert build_enter.payload.get("kwargs") == {}

    # Child of build_enter is the inner log + build exit
    build_enter_children = build_enter.children
    assert len(build_enter_children) == 2
    inner_log = next(
        (c for c in build_enter_children if c.event_type == "log"), None
    )
    build_exit = next(
        (c for c in build_enter_children if c.event_type == "exit"), None
    )
    assert inner_log is not None and build_exit is not None
    assert inner_log.message.strip() == "build_function"
    assert inner_log.payload is None
    assert build_exit.result.get("value") == "'test'"
    assert build_exit.payload is None

    # Add exit should also have the overall 'test' result
    assert add_exit.message.startswith("Exit")
    assert add_exit.result.get("value") == "'test'"
